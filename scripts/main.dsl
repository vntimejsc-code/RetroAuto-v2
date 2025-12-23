hotkeys {
  pause = "F7"
  start = "F5"
  stop = "F6"
}

flow main {
  click(button="left", clicks=2, use_match=false, x=1274, y=253);
  click(button="left", clicks=1, use_match=false, x=1274, y=299);
  click(button="left", clicks=1, use_match=false, x=1381, y=514);
  click(button="left", clicks=1, use_match=false, x=1298, y=463);
  click(button="left", clicks=1, use_match=false, x=1271, y=339);
  click(button="left", clicks=1, use_match=false, x=1301, y=243);
  click(button="left", clicks=1, use_match=false, x=1368, y=262);
  click(button="left", clicks=1, use_match=false, x=1341, y=273);
  click(button="left", clicks=1, use_match=false, x=1319, y=314);
  click(button="left", clicks=1, use_match=false, x=1317, y=378);
  wait_image("[target]", appear=true, timeout=10000);
  click_image("[target]");
}
