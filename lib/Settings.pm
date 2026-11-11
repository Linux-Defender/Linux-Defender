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
package ClamTk::Settings;

# use strict;
# use warnings;
$| = 1;

use File::Basename 'basename';
use File::Path 'make_path';

use Glib 'TRUE', 'FALSE';

use POSIX 'locale_h';
use Locale::gettext;

sub show_window {
    my $top_box = Gtk3::EventBox->new;

    my $box = Gtk3::Box->new( 'vertical', 0 );
    # $box->set_homogeneous(TRUE);
    $top_box->add( $box );

    my %prefs = ClamTk::Prefs->get_all_prefs();

    my $grid = Gtk3::Grid->new();
    $box->pack_start( $grid, FALSE, FALSE, 10 );
    $grid->set_column_spacing( 10 );
    $grid->set_column_homogeneous( TRUE );
    $grid->set_row_spacing( 10 );
    $grid->set_row_homogeneous( TRUE );

    my $option = Gtk3::CheckButton->new_with_label( _( 'Scan for PUAs' ) );
    $option->set_tooltip_text(
        _( 'Detect packed binaries, password recovery tools, and more' ) );
    $option->set_active( TRUE ) if ( $prefs{ Thorough } );
    $grid->attach( $option, 0, 0, 1, 1 );
    $option->signal_connect(
        toggled => sub {
            my $btn = shift;
            ClamTk::Prefs->set_preference( 'Thorough', $btn->get_active
                ? 1
                : 0 );
        }
    );

    $option
        = Gtk3::CheckButton->new_with_label( _( 'Use heuristic scanning' ) );
    # $option->set_tooltip_text(
    #     _( 'tooltip here' ) );
    $option->set_active( TRUE ) if ( $prefs{ Heuristic } );
    $grid->attach( $option, 0, 1, 1, 1 );
    $option->signal_connect(
        toggled => sub {
            my $btn = shift;
            ClamTk::Prefs->set_preference( 'Heuristic', $btn->get_active
                ? 1
                : 0 );
        }
    );

    $option = Gtk3::CheckButton->new_with_label(
        _( 'Scan files beginning with a dot (.*)' ) );
    $option->set_tooltip_text( _( 'Scan files typically hidden from view' ) );
    $option->set_active( TRUE ) if ( $prefs{ ScanHidden } );
    $grid->attach( $option, 0, 2, 1, 1 );
    $option->signal_connect(
        toggled => sub {
            my $btn = shift;
            ClamTk::Prefs->set_preference( 'ScanHidden', $btn->get_active
                ? 1
                : 0 );
        }
    );

    $option = Gtk3::CheckButton->new_with_label(
        _( 'Scan files larger than 20 MB' ) );
    $option->set_tooltip_text(
        _( 'Scan large files which are typically not examined' ) );
    $option->set_active( TRUE ) if ( $prefs{ SizeLimit } );
    $grid->attach( $option, 0, 3, 1, 1 );
    $option->signal_connect(
        toggled => sub {
            my $btn = shift;
            ClamTk::Prefs->set_preference( 'SizeLimit', $btn->get_active
                ? 1
                : 0 );
        }
    );

    $option = Gtk3::CheckButton->new_with_label(
        _( 'Scan directories recursively' ) );
    $option->set_tooltip_text(
        _( 'Scan all files and directories within a directory' ) );
    $option->set_active( TRUE ) if ( $prefs{ Recursive } );
    $grid->attach( $option, 0, 4, 1, 1 );
    $option->signal_connect(
        toggled => sub {
            my $btn = shift;
            ClamTk::Prefs->set_preference( 'Recursive', $btn->get_active
                ? 1
                : 0 );
        }
    );

    $option = Gtk3::CheckButton->new_with_label(
        _( 'Check for updates to this program' ) );
    $option->set_tooltip_text(
        _( 'Check online for application and signature updates' ) );
    $option->set_active( TRUE ) if ( $prefs{ GUICheck } );
    $grid->attach( $option, 0, 5, 1, 1 );
    $option->signal_connect(
        toggled => sub {
            my $btn = shift;
            ClamTk::Prefs->set_preference( 'GUICheck', $btn->get_active
                ? 1
                : 0 );
        }
    );

    my $rules_frame = Gtk3::Frame->new( _( 'Local YARA rules' ) );
    $box->pack_start( $rules_frame, FALSE, FALSE, 10 );
    my $rules_box = Gtk3::Box->new( 'vertical', 6 );
    $rules_box->set_border_width( 8 );
    $rules_frame->add( $rules_box );

    my $rules_path = ClamTk::App->get_path('yara_rules');
    make_path( $rules_path, { mode => 0700 } ) if !-d $rules_path;
    my $rules_note = Gtk3::Label->new(
        _( 'ClamAV can load compatible YARA rule files from this folder during scans. Only add rules from sources you trust; ClamTk does not download rule feeds.' )
    );
    $rules_note->set_line_wrap(TRUE);
    $rules_note->set_xalign(0.0);
    $rules_box->pack_start($rules_note, FALSE, FALSE, 0);

    my $rules_button = Gtk3::Button->new_with_label(
        _( 'Open local YARA rules folder' )
    );
    $rules_box->pack_start($rules_button, FALSE, FALSE, 0);
    $rules_button->signal_connect(
        clicked => sub {
            my $opener = ClamTk::App::_find_executable('xdg-open');
            if ($opener) {
                system( $opener, $rules_path ) == 0
                    or warn "Could not open YARA rules folder: $!\n";
            }
        }
    );

    my $infobar = Gtk3::InfoBar->new;
    #$box->pack_start( $infobar, FALSE, FALSE, 10 );
    $infobar->set_message_type( 'other' );
    my $use_image = ClamTk::Icons->get_image( 'go-previous' );
    $infobar->add_button( $use_image, -7 );
    $infobar->signal_connect(
        response => sub {
            ClamTk::GUI->swap_button;
            ClamTk::GUI->add_default_view;
        }
    );

    $top_box->show_all;
    return $top_box;
}

1;
