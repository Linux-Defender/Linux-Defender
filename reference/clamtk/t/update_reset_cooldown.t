use strict;
use warnings;
use Test::More;
use File::Temp qw(tempdir);
use File::Spec;

use FindBin;
require "$FindBin::Bin/../lib/Update.pm";

my $root = tempdir(CLEANUP => 1);
my $db = File::Spec->catdir($root, 'db');
my $conf = File::Spec->catfile($root, 'local.conf');
mkdir $db or die "Cannot create test database directory: $!";

{
    no warnings qw(redefine once);
    *ClamTk::App::get_path = sub {
        return { localfreshclamconf => $conf, db => $db };
    };
}

my $dat = File::Spec->catfile($db, 'freshclam.dat');

open my $fh, '>', $dat or die "Cannot create test state file: $!";
print {$fh} "test state\n";
close $fh;
open $fh, '>', $conf or die "Cannot create test config: $!";
print {$fh} "DatabaseMirror database.clamav.net\n";
close $fh;
ok(!ClamTk::Update::reset_cooldown(), 'does not reset state without a PrivateMirror');
ok(-e $dat, 'keeps updater state without a PrivateMirror');

open $fh, '>', $conf or die "Cannot write test config: $!";
print {$fh} "PrivateMirror https://mirror.example.test/clamav\n";
close $fh;
ok(ClamTk::Update::reset_cooldown(), 'resets state when PrivateMirror is configured');
ok(!-e $dat, 'removes only the test updater state file');

open $fh, '>', $conf or die "Cannot write test config: $!";
print {$fh} "PrivateMirror https://mirror.example.test/clamav\n";
close $fh;
ok(!ClamTk::Update::reset_cooldown(), 'handles a missing updater state file');

done_testing();
