import msvcrt

z = 0
print("starting")
while z == 0:
    c = msvcrt.getch().decode()
    print(c)
    if c == "w":
        print("up")
    elif c == "s":
        print("down")
    elif c == "a":
        print("left")
    elif c == "d":
        print("right")
    elif c == "x":
        z = 1
    elif c == 'q':
        break
    else:
        print("not valid")
