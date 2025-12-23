hotkeys {
  pause = "F7"
  start = "F5"
  stop = "F6"
}

flow main {
  wait_image("capture_2", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  if_image("capture_2");
  wait_image("capture_1", appear=true, timeout=10000);
  if_image("capture_2");
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  wait_image("capture_1", appear=true, timeout=10000);
  wait_image("capture_2", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  wait_image("capture_1", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1270, y=356);
  click(button="left", clicks=1, use_match=false, x=1234, y=406);
  if_image("capture_1");
  sleep(1000);
  if_image("capture_2");
  wait_image("[target]", appear=true, timeout=10000);
  sleep(1000);
  wait_image("capture_2", appear=true, timeout=10000);
  if_image("capture_1");
  click(button="left", clicks=2, use_match=false, x=1291, y=483);
  click(button="left", clicks=2, use_match=false, x=1269, y=553);
  click(button="left", clicks=2, use_match=false, x=1298, y=634);
  click(button="left", clicks=2, use_match=false, x=1306, y=625);
  click(button="left", clicks=2, use_match=false, x=1277, y=512);
  click(button="left", clicks=2, use_match=false, x=1307, y=415);
  click(button="left", clicks=2, use_match=false, x=1306, y=625);
  click(button="left", clicks=2, use_match=false, x=1277, y=512);
  click(button="left", clicks=2, use_match=false, x=1298, y=634);
  click(button="left", clicks=2, use_match=false, x=1307, y=415);
  wait_image("capture_2", appear=true, timeout=10000);
  wait_image("capture_2", appear=true, timeout=10000);
  click(button="left", clicks=2, use_match=false, x=1467, y=389);
  click(button="left", clicks=2, use_match=false, x=1048, y=467);
  click(button="left", clicks=2, use_match=false, x=613, y=486);
  click(button="left", clicks=2, use_match=false, x=544, y=290);
  click(button="left", clicks=2, use_match=false, x=1480, y=514);
}
