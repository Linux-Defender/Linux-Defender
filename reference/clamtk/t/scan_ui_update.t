use strict;
use warnings;
use Test::More;
use FindBin;
require "$FindBin::Bin/../lib/Scan.pm";

ok(
    ClamTk::Scan::_scan_ui_update_due( 100.0, 0, 0.1 ),
    'first scan detail refresh is due'
);
ok(
    !ClamTk::Scan::_scan_ui_update_due( 100.05, 100.0, 0.1 ),
    'skips refreshes inside the 100 ms interval'
);
ok(
    ClamTk::Scan::_scan_ui_update_due( 100.101, 100.0, 0.1 ),
    'refreshes again once the 100 ms interval elapses'
);

done_testing();
