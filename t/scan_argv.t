use strict;
use warnings;
use Test::More;
use FindBin;

require "$FindBin::Bin/../lib/Scan.pm";

my $target    = '/tmp/file with spaces;$(touch should-not-run)';
my $excluded  = "/home/user/one folder;\$(touch should-not-run)/O'Reilly";
my $directive = '--scan-mail=no --exclude-dir='
    . ClamTk::Scan::_quote_shellword($excluded);
my @argv = ClamTk::Scan::_scan_argv(
    '/usr/bin/clamscan', $directive, $target,
    '--database=/home/user/.config/clamtk/db'
);
my @hidden_exclude = ClamTk::Scan::_scan_argv(
    '/usr/bin/clamscan',
    ' ' . ClamTk::Scan::_quote_shellword('--exclude=\\/\\.'),
    $target
);

is( $argv[0], '/usr/bin/clamscan', 'uses the executable path directly' );
is( $argv[1], '--no-summary', 'keeps default scanner output option' );
is( $argv[2], '--block-encrypted', 'keeps encrypted-file warning option' );
is(
    $argv[3], '--database=/home/user/.config/clamtk/db',
    'passes the database path as one argument'
);
is( $argv[5], "--exclude-dir=$excluded", 'preserves spaces and metacharacters in an exclude path' );
is( $argv[-1], $target, 'passes the scan target literally as one argument' );
is( $hidden_exclude[3], '--exclude=\\/\\.', 'preserves the hidden-file exclusion regex' );

done_testing();
