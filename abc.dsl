// RetroScript 9.0
// Press F5 to run, F6 to stop

@config
  timeout = 30s
  loop_limit = 1000
  click_delay = 50..100ms
  on_error = pause

@hotkeys
  start = "F5"
  stop = "F6"
  pause = "F7"

@main:
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: None, y: None, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  if_image("capture_2")
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  wait_image("capture_2", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  wait_image("capture_1", timeout: 10000, appear: true)
  click(x: 1270, y: 356, button: "left", clicks: 2, use_match: false)
  click(x: 1234, y: 406, button: "left", clicks: 1, use_match: false)
  if_image("capture_1")
  sleep(1000)
  if_image("capture_2")
  wait_image("[target]", timeout: 10000, appear: true)
  click(x: None, y: None, button: "left", clicks: 1, use_match: false)
  sleep(1000)
  wait_image("capture_2", timeout: 10000, appear: true)
  if_image("capture_1")
  click(x: 1291, y: 483, button: "left", clicks: 2, use_match: false)
  click(x: 1269, y: 553, button: "left", clicks: 2, use_match: false)
  click(x: 1298, y: 634, button: "left", clicks: 2, use_match: false)
  click(x: 1306, y: 625, button: "left", clicks: 2, use_match: false)
  click(x: 1277, y: 512, button: "left", clicks: 2, use_match: false)
  click(x: 1307, y: 415, button: "left", clicks: 2, use_match: false)
  click(x: 1306, y: 625, button: "left", clicks: 2, use_match: false)
  click(x: 1277, y: 512, button: "left", clicks: 2, use_match: false)
  click(x: 1298, y: 634, button: "left", clicks: 2, use_match: false)
  goto 
  click(x: 1307, y: 415, button: "left", clicks: 2, use_match: false)
  wait_image("capture_2", timeout: 10000, appear: true)
  wait_image("capture_2", timeout: 10000, appear: true)
  click(x: 1467, y: 389, button: "left", clicks: 2, use_match: false)
  click(x: 1048, y: 467, button: "left", clicks: 2, use_match: false)
  click(x: 613, y: 486, button: "left", clicks: 2, use_match: false)
  click(x: 544, y: 290, button: "left", clicks: 2, use_match: false)
  click(x: 1480, y: 514, button: "left", clicks: 2, use_match: false)
