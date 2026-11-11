use strict;
use warnings;
use Test::More;
use FindBin;

require "$FindBin::Bin/../lib/Update.pm";

ok(
    ClamTk::Update::_freshclam_succeeded( 1, 0 ),
    'accepts a successful FreshClam exit'
);
ok(
    !ClamTk::Update::_freshclam_succeeded( 0, 0 ),
    'rejects a failed pipe close'
);
ok(
    !ClamTk::Update::_freshclam_succeeded( 1, 256 ),
    'rejects a nonzero child exit status'
);

done_testing();
