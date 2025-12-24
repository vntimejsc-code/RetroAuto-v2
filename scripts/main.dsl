hotkeys {
  pause = "F7"
  start = "F5"
  stop = "F6"
}

flow main {
    # Flat check 1
    if if_image("capture_1") {
        click(button="left", clicks=3, use_match=false, x=1, y=1);
    }
    
    # Flat check 2
    if if_image("capture_2") {
        if if_image("capture_4") {
            click(button="left", clicks=2, use_match=false, x=1, y=1);
        }
    }
    
    # Flat check 3
    if if_image("capture_3") {
        if if_image("capture_5") {
            click(button="left", clicks=2, use_match=false, x=1, y=1);
        }
    }
}