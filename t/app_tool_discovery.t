use strict;
use warnings;
use Test::More;
use File::Temp 'tempdir';
use File::Spec;
use FindBin;

require "$FindBin::Bin/../lib/App.pm";

my $directory = tempdir( CLEANUP => 1 );
my $tool      = File::Spec->catfile( $directory, 'freshclam' );
open( my $fh, '>', $tool ) or die "create fake executable: $!";
print {$fh} "#!/bin/sh\nexit 0\n";
close $fh or die "close fake executable: $!";
chmod 0755, $tool or die "chmod fake executable: $!";

{
    local $ENV{ PATH } = $directory;
    is(
        ClamTk::App::_find_executable('freshclam'),
        $tool,
        'finds a tool installed in a custom PATH directory'
    );
}

is(
    ClamTk::App::_find_executable('missing-clamtk-test-tool'),
    '',
    'returns an empty path when no executable is available'
);

done_testing();
