
from LpmsConfig import LPMS_STREAM_FREQ
class LpmsConfigurationSettings(object):

    def __init__(self):
        self.initial_streaming_mode = 0
        self.output_360 = 0
        self.output_rad = 0
        self.stream_frequency = 0
        self.uart_baudrate = 0

    def __str__(self):
        j = 50
        d = '.'
        res = ""
        res += "# Configuration Register #" + "\n"
        res += "[ 0   ] Initial Streaming mode".ljust(j, d) + str(self.initial_streaming_mode) + "\n"
        res += "[ 1   ] 360 output".ljust(j, d) + str(self.output_360) + "\n"
        res += "[ 2   ] rad output".ljust(j, d) + str(self.output_rad) + "\n"
        res += "[ 3:4 ] Stream Frequency".ljust(j, d) + str(self.stream_frequency) + "\n"
        return res

    def pretty_print(self):
        print self.__str__()

    def parse(self, cr):
        l = ("{0:b}".format(cr)).zfill(32)
        self.initial_streaming_mode = l[-1]
        self.output_360 = l[-2]
        self.output_rad = l[-3]
        self.stream_frequency = LPMS_STREAM_FREQ[int(l[-6:-3],2)]
     