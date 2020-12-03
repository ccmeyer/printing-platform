from .exceptions import MFCS_NoMFCS, MFCS_NoChannel

error_messages = {1: "PGMFC not connected",
                  2: "Fail Open Session",
                  3: "This channel does not exist on this PGMFC",

                  100: "Illegal Input",
                  101: "Invalid PGMFC",
                  200: "No response",
                  201: "No data found"
                  }

def parse_error(c_error):
    if c_error == 1:
        raise MFCS_NoMFCS(error_messages[c_error])
    if c_error == 3:
        raise MFCS_NoChannel(error_messages[c_error])
    if c_error == 2:
        print(error_messages[c_error])
    if c_error == 100 or c_error == 101:
        print(error_messages[c_error])
    if c_error == 200 or c_error == 201:
        print(error_messages[c_error])


