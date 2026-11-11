# ClamTk, copyright (C) 2004-2024 Dave M
#
# This file is part of ClamTk
# https://github.com/dave-theunsub/clamtk/
# https://gitlab.com/dave_m/clamtk/
#
# ClamTk is free software; you can redistribute it and/or modify it
# under the terms of either:
#
# a) the GNU General Public License as published by the Free Software
# Foundation; either version 1, or (at your option) any later version, or
#
# b) the "Artistic License".
package ClamTk::Analysis;

use Glib 'TRUE', 'FALSE';

# use strict;
# use warnings;
$| = 1;

use LWP::UserAgent;
use LWP::Protocol::https;
use File::Basename 'basename';
use File::Copy 'move';
use Text::CSV;
use ClamTk::VirusTotal;

use POSIX 'locale_h';
use Locale::gettext;

binmode STDIN, ":encoding(UTF-8)";

my $store;            # Liststore results
my $model;            # ListStore for combobox
my $combobox;         # ComboBox for previous analysis
my $nb;               # Notebook
my $filename = '';    # name of file analyzed
my $bar;              # InfoBar
my $window;           # Dialog; global for queue_draw;
my $submitted = 0;    # Boolean value to keep track if file
                      # has been submitted or not
my $from_scan;

sub show_window {
    ( undef, $from_scan, $parent ) = @_;
    $window
        = Gtk3::Dialog->new( undef, $parent,
        [ qw| modal destroy-with-parent use-header-bar | ],
        );
    $window->signal_connect(
        destroy => sub {
            $window->destroy;
            1;
        }
    );
    $window->set_border_width( 5 );
    $window->set_default_size( 450, 250 );
    $window->set_position( 'mouse' );

    my $hb = Gtk3::HeaderBar->new;
    $hb->set_title( _( 'Analysis' ) );
    $hb->set_show_close_button( TRUE );
    $hb->set_decoration_layout( 'menu:close' );

    my $images_dir = ClamTk::App->get_path( 'images' );
    my $pixbuf
        = Gtk3::Gdk::Pixbuf->new_from_file_at_size( "$images_dir/clamtk.png",
        24, 24 );
    my $image = Gtk3::Image->new;
    $image->set_from_pixbuf( $pixbuf );
    my $button = Gtk3::ToolButton->new( $image, '' );
    $button->set_sensitive( FALSE );
    $button->set_tooltip_text( _( 'ClamTk Virus Scanner' ) );
    $hb->pack_start( $button );
    $window->set_titlebar( $hb );

    my $help_message = _(
        "VirusTotal can provide a report from many security vendors. ClamTk first sends the selected file's SHA-256 hash after you confirm. If no report exists, a separate confirmation is required before ClamTk uploads the file. Standard submissions may be shared with VirusTotal's examining partners. Never submit confidential files or files containing personal information."
    );

    my $help_btn  = Gtk3::ToolButton->new();
    my $use_image = ClamTk::Icons->get_image( 'system-help' );
    $help_btn->set_label( _( 'Help' ) );
    $help_btn->set_icon_name( $use_image );
    $help_btn->set_is_important( TRUE );
    $help_btn->set_tooltip_text( _( 'What is this?' ) );
    $help_btn->signal_connect( clicked => sub { popup( $help_message ) } );
    $hb->pack_start( $help_btn );

    my $key_btn = Gtk3::ToolButton->new();
    $key_btn->set_icon_name('dialog-password');
    $key_btn->set_label( _( 'VirusTotal key' ) );
    $key_btn->set_tooltip_text(
        _( 'Store your personal VirusTotal API key in the desktop keyring' )
    );
    $key_btn->signal_connect( clicked => sub { configure_api_key() } );
    $hb->pack_end($key_btn);

    my $box = Gtk3::Box->new( 'vertical', 5 );
    $box->set_homogeneous( FALSE );
    $window->get_content_area->add( $box );

    $nb = Gtk3::Notebook->new;
    $box->pack_start( $nb, TRUE, TRUE, 0 );

    #<<<
    # Add initial page (select file, etc)
    $nb->insert_page(
        page_one(),
        Gtk3::Label->new( _( 'File Analysis' ) ),
        0,
    );

    # Add results page
    $nb->insert_page(
        page_two(),
        Gtk3::Label->new( _( 'Results' ) ),
        1,
    );
    #>>>

    $bar = Gtk3::InfoBar->new;
    $box->pack_start( $bar, FALSE, FALSE, 0 );
    $bar->set_message_type( 'other' );

    # $bar->add_button( 'gtk-close', -7 );
    $bar->add_button( _( 'Close' ), -7 );
    $bar->signal_connect(
        response => sub {
            $submitted = 0;
            $window->destroy;
        }
    );

    $window->show_all;
    $window->run;
    $window->destroy;
    1;
}

sub page_one {

    # Analysis page
    my $box = Gtk3::Box->new( 'vertical', 5 );
    $box->set_homogeneous( FALSE );

    my $separator = Gtk3::Separator->new( 'horizontal' );

    $box->pack_start( analysis_frame_one(), FALSE, FALSE, 5 );
    $box->pack_start( $separator,           FALSE, FALSE, 5 );
    $box->pack_start( analysis_frame_two(), FALSE, FALSE, 5 );

    return $box;
}

sub page_two {

    # Results page
    my $box = Gtk3::VBox->new( FALSE, 0 );

    my $sw = Gtk3::ScrolledWindow->new( undef, undef );
    $sw->set_policy( 'never', 'automatic' );
    $box->pack_start( $sw, TRUE, TRUE, 0 );

    use constant VENDOR => 0;
    use constant RESULT => 1;
    use constant DATE   => 2;

    #<<<
    $store = Gtk3::ListStore->new(
            # VENDOR
            'Glib::String',
            # RESULT
            'Glib::String',
            # DATE
            'Glib::String',
    );

    my $tree = Gtk3::TreeView->new_with_model( $store );
    $tree->set_rules_hint( TRUE );
    $sw->add( $tree );

    my $renderer = Gtk3::CellRendererText->new;
    my $column
        = Gtk3::TreeViewColumn->new_with_attributes(
                _( 'Vendor' ),
                $renderer,
                text => VENDOR,
    );
    $column->set_expand( TRUE );
    $column->set_sort_column_id( VENDOR );
    $tree->append_column( $column );

    $column = Gtk3::TreeViewColumn->new_with_attributes(
                _( 'Date' ),
                $renderer,
                text => DATE,
    );
    $column->set_sort_column_id( DATE );
    $column->set_expand( TRUE );
    $tree->append_column( $column );

    $column = Gtk3::TreeViewColumn->new_with_attributes(
                _( 'Result' ),
                $renderer,
                text => RESULT,
    );
    $column->set_expand( TRUE );
    $column->set_sort_column_id( RESULT );
    $tree->append_column( $column );
    #>>>

    my $toolbar = Gtk3::Toolbar->new;
    $box->pack_start( $toolbar, FALSE, FALSE, 3 );
    $toolbar->set_style( 'both-horiz' );

    my $separator = Gtk3::SeparatorToolItem->new;
    $separator->set_draw( FALSE );
    $separator->set_expand( TRUE );
    $toolbar->insert( $separator, -1 );

    my $button = Gtk3::ToolButton->new();
    $button->set_icon_name( 'document-save-as' );
    $button->set_label( _( 'Save results' ) );

    # $button->set_tooltip_text( _( 'Save results' ) );
    $toolbar->insert( $button, -1 );
    $button->signal_connect(
        clicked => sub {
            return unless ( $store->iter_n_children );
            save_file();
        }
    );

    return $box;
}

sub analysis_frame_one {
    my $box = Gtk3::Box->new( 'vertical', 5 );
    $box->set_homogeneous( FALSE );

    my $label
        = Gtk3::Label->new( _( "Check or recheck a file's reputation" ) );
    $label->set_alignment( 0.0, 0.5 );
    $box->pack_start( $label, FALSE, FALSE, 5 );

    my $grid = Gtk3::Grid->new();
    $box->pack_start( $grid, FALSE, FALSE, 5 );
    $grid->set_column_spacing( 10 );
    $grid->set_column_homogeneous( FALSE );
    $grid->set_row_spacing( 10 );
    $grid->set_row_homogeneous( TRUE );

    #<<<
    # Declaring this now for setting sensitive/insensitive
    my $button = Gtk3::ToolButton->new();
    my $use_image = ClamTk::Icons->get_image('edit-select');
    $button->set_icon_name($use_image);

    my $select_button
        = Gtk3::FileChooserButton->new(
                _( 'Select a file' ),
                'open',
    );

    # If we've arrived from scanning results, set the file:
    if( $from_scan ) {
            $select_button->set_filename( $from_scan );
    }
    $button->set_sensitive( TRUE );
    $select_button->set_hexpand(TRUE);

    $select_button->set_current_folder(
        ClamTk::App->get_path( 'directory' )
    );
    $grid->attach( $select_button, 0, 0, 1, 1 );
    #>>>

    my $separator = Gtk3::SeparatorToolItem->new;
    $separator->set_draw( FALSE );
    $grid->attach( $separator, 1, 0, 1, 1 );

    $grid->attach( $button, 2, 0, 1, 1 );
    $button->set_tooltip_text( _( 'Submit file for analysis' ) );

    $button->signal_connect(
        clicked => sub {
            $filename = $select_button->get_filename;
            return unless -e $filename;

            $submitted++;

            if ( !ClamTk::VirusTotal::api_key() ) {
                popup(
                    _( 'Set your personal VirusTotal API key with the key button in this window before checking a file.' )
                );
                return;
            }

            my $hash_warning
                = _(
                "ClamTk will send this file's SHA-256 hash to VirusTotal to look for an existing report. This does not upload the file, but VirusTotal may add queried indicators to its dataset. Continue only if sharing the hash is okay."
                );
            my $hash_dialog = Gtk3::MessageDialog->new(
                $window,
                [ qw( modal destroy-with-parent ) ],
                'warning', 'ok-cancel', $hash_warning
            );
            my $hash_confirm = $hash_dialog->run;
            $hash_dialog->destroy;
            return if $hash_confirm ne 'ok';

            # Gtk3::main_iteration while Gtk3::events_pending;
            my ( $vt_results, $new_window, $is_error )
                = check_for_existing( $filename );

            # Information exists on this file; show results
            if ( $new_window ) {
                $nb->show_all;
                $nb->set_current_page( 1 );

                #} elsif ( $new_window && !$is_error ) {
            } elsif ( $vt_results == 0 ) {

                # The public upload endpoint accepts files up to 32 MB.
                my $size = -s $filename;
                if ( $size > 32 * 1024 * 1024 ) {
                    popup( _( 'VirusTotal uploads through this integration are limited to 32 MB.' ) );
                    return;
                }

                my $warn_message
                    = _(
                    "Please note you should never submit sensitive files to Virustotal.  Any uploaded file can be viewed by Virustotal customers. Do not submit anything with personal information or passwords."
                    );

                # No information exists; offer to submit file
                my $dialog
                    = Gtk3::MessageDialog->new( $window,
                    [ qw( modal destroy-with-parent ) ],
                    'warning', 'ok-cancel', $warn_message, );

                my $confirm = $dialog->run;
                $dialog->destroy;

                if ( $confirm eq _( 'ok' ) ) {
                    $submitted++;
                    submit_new();
                    return;
                } else {
                    warn "cancelled submission\n";
                    return;
                }
            } else {
                popup( _( 'Unable to submit file: try again later' ) );
                return;
            }
        }
    );

    return $box;
}

sub analysis_frame_two {
    my $box = Gtk3::Box->new( 'vertical', 5 );
    $box->set_homogeneous( FALSE );

    my $label = Gtk3::Label->new( _( 'View or delete previous results' ) );
    $label->set_alignment( 0.0, 0.5 );
    $box->pack_start( $label, FALSE, FALSE, 0 );

    my $grid = Gtk3::Grid->new();
    $box->pack_start( $grid, FALSE, FALSE, 5 );
    $grid->set_column_spacing( 10 );
    $grid->set_column_homogeneous( FALSE );
    $grid->set_row_spacing( 10 );
    $grid->set_row_homogeneous( TRUE );

    $model = Gtk3::ListStore->new( 'Glib::String' );

    $combobox = Gtk3::ComboBox->new_with_model( $model );
    $combobox->set_hexpand( TRUE );
    $grid->attach( $combobox, 0, 0, 1, 1 );
    my $render = Gtk3::CellRendererText->new;
    $combobox->pack_start( $render, TRUE );
    $combobox->add_attribute( $render, text => 0 );
    read_files();

    my $separator = Gtk3::SeparatorToolItem->new;
    $separator->set_draw( FALSE );
    $grid->attach( $separator, 1, 0, 1, 1 );

    my $button = Gtk3::ToolButton->new();
    $button->set_icon_name( 'text-x-preview' );
    $button->set_tooltip_text( _( 'View file results' ) );
    $grid->attach( $button, 2, 0, 1, 1 );
    $button->signal_connect(
        clicked => sub {

            # my $file = $combobox->get_active_text;
            my $iter = $combobox->get_active_iter();
            return unless ( $model->iter_is_valid( $iter ) );
            my $file = $model->get_value( $iter, 0 );
            return unless ( $file );
            my $file_to_use = '';
            my $files       = read_files();

            # Written so as to not choke older Perls
            for my $key ( sort @$files ) {
                if ( $key->{ basefilepath } eq $file ) {
                    $file_to_use = $key->{ readpath };
                }
            }

            # For some reason, we'll use csv files
            my $csv = Text::CSV->new( { binary => 1, eol => "\n" } )
                or do {
                warn "Unable to begin Text::CSV: $!\n";
                return;
                };

            open( my $f, '<:encoding(utf8)', $file_to_use ) or do {
                warn "Unable to opening VT CSV file: $!\n";

                # popup( _( 'Error opening VT CSV file' ) );
                return;
            };

            # File, Hash, Date
            my $fields;
            my $counter = 0;
            while ( my $row = <$f> ) {
                chomp( $row );
                next if ( $row =~ /^#/ );
                next if ( $row =~ /^\s*$/ );
                if ( $csv->parse( $row ) ) {
                    $fields->[ $counter ] = [ $csv->fields() ];
                    $counter++;
                }
            }
            close( $f );
            $store->clear;

            #<<<
            # Written so as to not choke older Perls
            for my $v ( sort @{ $fields } ) {
                my $iter = $store->append;
                $store->set(
                    $iter,
                    VENDOR, $v->[0],
                    RESULT, $v->[1],
                    DATE, $v->[2],
            );
            #>>>
            }
            $nb->show_all;
            $nb->set_current_page( 1 );
        }
    );

    $button = Gtk3::ToolButton->new();
    $button->set_icon_name( 'edit-delete' );
    $button->set_tooltip_text( _( 'Delete file results' ) );
    $grid->attach( $button, 3, 0, 1, 1 );
    $button->signal_connect(
        clicked => sub {
            my $file_to_use = '';
            my $iter        = $combobox->get_active_iter();
            return unless ( $model->iter_is_valid( $iter ) );
            my $file = $model->get_value( $iter, 0 );
            return unless ( $file );
            my $files = read_files();

            # This has to be written a certain way so
            # that older Perls don't $choke
            for my $key ( sort @{ $files } ) {
                if ( $key->{ basefilepath } eq $file ) {
                    $file_to_use = $key->{ readpath };

                    if ( -e $file_to_use ) {
                        unlink( $file_to_use ) or do {
                            warn "Unable to delete VT $file_to_use: $!\n";
                            return;
                        };
                        $combobox->set_active( -1 );
                    }
                    read_files();

                    # we're done!
                    last;
                }
            }
        }
    );

    return $box;
}

sub read_files {
    my $submit_dir = ClamTk::App->get_path( 'submit' );
    my $results;

    $model->clear;

    my $arr_count = 0;

    # Grab all files
    for my $f ( glob "$submit_dir/*" ) {
        my $basename = basename( $f );

        # Might be other garbage in the folder; just
        # look for ones that look like hashes
        next unless ( length $basename == 64 );
        $results->[ $arr_count ]->{ readpath } = $f;
        $results->[ $arr_count ]->{ hash }     = basename( $f );
        open( my $t, '<:encoding(utf8)', $f ) or do {
            warn "Unable to open analysis file >$f<: $!\n";
            next;
        };
        while ( <$t> ) {
            chomp;
            if ( /^# File (.*?)$/ ) {
                $results->[ $arr_count ]->{ filepath }     = $1;
                $results->[ $arr_count ]->{ basefilepath } = basename( $1 );
                $model->set( $model->append, 0,
                    basename( $results->[ $arr_count ]->{ filepath } ) );
                last;
            }
        }
        close( $t );
        $arr_count++;
    }
    return $results;
}

sub check_for_existing {
    set_infobar_mode( _( 'Please wait...' ) );
    $window->queue_draw;

    my $file = shift;
    my $hash = get_hash($file);
    my $report = ClamTk::VirusTotal::check_hash( $hash, add_ua_proxy() );
    set_infobar_mode( ' ' );

    if ( $report->{status} eq 'found' ) {
        for my $row ( @{ $report->{results} } ) {
            my $iter = $store->append;
            $store->set(
                $iter,
                VENDOR, $row->[0],
                RESULT, $row->[1],
                DATE,   $row->[2]
            );
        }
        return ( 1, TRUE, FALSE );
    }
    return ( 0, FALSE, FALSE ) if $report->{status} eq 'not-found';
    warn "VirusTotal lookup failed: $report->{status}\n";
    return ( -4, FALSE, TRUE );
}

sub submit_new {

    # First, set the infobar so the user knows
    # something is happening:
    set_infobar_mode( _( 'Please wait...' ) );
    $window->queue_draw;
    my $response = ClamTk::VirusTotal::submit_file(
        $filename, add_ua_proxy()
    );

    set_infobar_mode( ' ' );
    $bar->show_all;
    $window->queue_draw;

    if ( $response->{status} eq 'accepted' ) {

        # Save off the results; might use them later
        my $file = ClamTk::App->get_path( 'virustotal_links' );
        my $hash = get_hash( $filename );

        open( my $f, '>>:encoding(UTF-8)', $file );

        # or warn "Unable to save virustotal results: $!\n";
        my $csv = Text::CSV->new( { binary => 1, eol => "\n" } );
        my $ref;
        $ref->[ 0 ] = [ $filename, $hash,
            "https://www.virustotal.com/gui/file/$hash" ];
        $csv->print( $f, $_ ) for ( @$ref );
        close( $f );

        popup( _( 'File successfully submitted for analysis.' ) );
    } else {
        popup( _( 'Unable to submit file: try again later' ) );
    }
}

sub configure_api_key {
    my $dialog = Gtk3::Dialog->new(
        _( 'Configure VirusTotal API key' ), $window,
        [ qw( modal destroy-with-parent ) ]
    );
    $dialog->add_button( _( 'Cancel' ), 'cancel' );
    $dialog->add_button( _( 'Save' ),   'ok' );

    my $content = $dialog->get_content_area;
    my $label = Gtk3::Label->new(
        _( 'Your key is saved in the desktop keyring and is never stored in the ClamTk source or preferences.' )
    );
    $label->set_line_wrap(TRUE);
    $content->pack_start($label, FALSE, FALSE, 8);

    my $entry = Gtk3::Entry->new;
    $entry->set_visibility(FALSE);
    $entry->set_placeholder_text( _( 'Paste your personal VirusTotal API key' ) );
    $content->pack_start($entry, FALSE, FALSE, 8);
    $dialog->show_all;
    my $response = $dialog->run;
    my $key = $entry->get_text;
    $dialog->destroy;

    return if $response ne 'ok';
    if ( ClamTk::VirusTotal::save_api_key($key) ) {
        popup( _( 'VirusTotal API key saved to the desktop keyring.' ) );
    } else {
        popup( _( 'Could not save the key. Check that a Secret Service keyring is installed and unlocked.' ) );
    }
}

sub get_hash {
    my ($file) = @_;
    my $hash = ClamTk::VirusTotal::sha256_file($file);
    warn "Unable to read >$file< for hashing: $!\n" if !defined $hash;
    return $hash;
}

sub save_file {

    # VENDOR, RESULT, DATE
    # temporary filename
    my $hash = get_hash( $filename );
    my $file = ClamTk::App->get_path( 'submit' ) . '/' . $hash;

    my $ref;
    my $count = 0;

    $store->foreach(
        sub {
            my ( $liststore, $path, $iter ) = @_;
            my ( $vendor, $result, $date )
                = $liststore->get( $iter, 0, 1, 2 );
            $ref->[ $count ] = [ $vendor, $result, $date ];
            $count++;
            return FALSE;
        }
    );

    # For some reason, we'll use csv files
    my $csv = Text::CSV->new( { binary => 1, eol => "\n" } )
        or do {
        popup( _( 'Unable to save file' ) );
        return;
        };

    open( my $f, '>:encoding(utf8)', $file ) or do {
        popup( _( 'Unable to save file' ) );
        return;
    };
    print $f '# File', ' ', $filename,        "\n";
    print $f '# Hash', ' ', $hash,            "\n";
    print $f '# Date', ' ', scalar localtime, "\n\n";
    $csv->print( $f, $_ ) for ( @$ref );
    close( $f );

    popup( _( 'File has been saved' ) );
    read_files();

    return TRUE;
}

sub popup {
    my ( $message, $option ) = @_;

    my $dialog = Gtk3::MessageDialog->new(
        undef,    # no parent
        [ qw| modal destroy-with-parent | ],
        'info',
        $option ? 'ok-cancel' : 'close',
        $message,
    );

    if ( 'ok' eq $dialog->run ) {
        $dialog->destroy;
        return TRUE;
    }
    $dialog->destroy;

    return FALSE;
}

sub set_infobar_mode {
    my $text = shift;

    for my $c ( $bar->get_content_area->get_children ) {
        if ( $c->isa( 'Gtk3::Label' ) ) {
            $c->set_text( $text );
            $bar->show_all;
            $window->queue_draw;
            return;
        }
    }

    # We don't have a Label, so make one:
    my $label = Gtk3::Label->new( $text );
    $label->set_use_markup( TRUE );
    $bar->get_content_area->add( $label );
    $bar->show_all;
    $window->queue_draw;

    return;
}

sub add_ua_proxy {
    my $agent = LWP::UserAgent->new( ssl_opts => { verify_hostname => 1 } );

    my $local_tk_version = ClamTk::App->get_TK_version();
    $agent->agent( "ClamTk/$local_tk_version" );
    $agent->timeout( 60 );

    $agent->protocols_allowed( [ 'http', 'https' ] );

    if ( ClamTk::Prefs->get_preference( 'HTTPProxy' ) ) {
        if ( ClamTk::Prefs->get_preference( 'HTTPProxy' ) == 1 ) {
            $agent->env_proxy;
        } elsif ( ClamTk::Prefs->get_preference( 'HTTPProxy' ) == 2 ) {
            my $path = ClamTk::App->get_path( 'db' );
            $path .= '/local.conf';
            my ( $url, $port );
            if ( -e $path ) {
                if ( open( my $FH, '<', $path ) ) {
                    while ( <$FH> ) {
                        if ( /HTTPProxyServer\s+(.*?)$/ ) {
                            $url = $1;
                        }
                        last if ( !$url );
                        if ( /HTTPProxyPort\s+(\d+)$/ ) {
                            $port = $1;
                        }
                    }
                    close( $FH );
                    $agent->proxy( http  => "$url:$port" );
                    $agent->proxy( https => "$url:$port" );
                    $ENV{ HTTPS_PROXY }                  = "$url:$port";
                    $ENV{ HTTP_PROXY }                   = "$url:$port";
                    $ENV{ HTTPS_DEBUG }                  = 1;
                }
            }
        }
    }

    return $agent;
}

sub button_test {

    # So, this is a test to determine if set_filename works,
    # which is tested by seeing if we can get_filename.
    # Return TRUE if it succeeds so we can add the Analysis
    # button to the Results window.
    # Otherwise return FALSE, and don't draw it.
    my $fcb = Gtk3::FileChooserButton->new( 'just a test', 'open', );
    $fcb->set_filename( '/usr/bin/clamtk' );
    if ( $fcb->get_filename ) {
        return TRUE;
    } else {
        return FALSE;
    }
}

1;
