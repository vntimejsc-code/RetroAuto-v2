hotkeys {
  pause = "F7"
  start = "F5"
  stop = "F6"
}

flow main {
  if_image("capture_1");
  if_image("capture_5");
  click(button="left", clicks=3, use_match=false, x=1, y=1);
   if_image("capture_2");
  if_image("capture_4");
  click(button="left", clicks=2, use_match=false, x=1, y=1);
}
