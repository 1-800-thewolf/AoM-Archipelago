extern int gAPCategory = -1;

void main()
{
   gAPCategory = aiAddEchoCategory("Archipelago");
   aiEcho("APAI startup.");
}

rule APHeartbeat
minInterval 30
active
{
   aiEcho("APAI heartbeat.");
}

// -----------------------------------------------------------------------
// AUTO-GENERATED AP BRIDGE FUNCTIONS
// The client rewrites this file on connect by loading this template from
// aom.apworld/triggers/ap_ai_runtime.xs and appending:
//   - APCheck_<locid>()
//   - APLocked_<campaign>()
//   - APShop_<slot>()
// -----------------------------------------------------------------------
