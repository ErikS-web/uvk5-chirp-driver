# Quansheng UV-K5 driver (c) 2023 Jacek Lipkowski <sq5bpf@lipkowski.org>
# Adapted For UV-K5 EGZUMER custom software By EGZUMER, JOC2 
#
# based on template.py Copyright 2012 Dan Smith <dsmith@danplanet.com>
#
#
# This is a preliminary version of a driver for the UV-K5
# It is based on my reverse engineering effort described here:
# https://github.com/sq5bpf/uvk5-reverse-engineering
#
# Warning: this driver is experimental, it may brick your radio,
# eat your lunch and mess up your configuration.
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import struct
import logging
                
from chirp import chirp_common, directory, bitwise, memmap, errors, util
from chirp.settings import RadioSetting, RadioSettingGroup, \
    RadioSettingValueBoolean, RadioSettingValueList, \
    RadioSettingValueInteger, RadioSettingValueString, \
    RadioSettings, InvalidValueError

LOG = logging.getLogger(__name__)

# Show the obfuscated version of commands. Not needed normally, but
# might be useful for someone who is debugging a similar radio
DEBUG_SHOW_OBFUSCATED_COMMANDS = False

# Show the memory being written/received. Not needed normally, because
# this is the same information as in the packet hexdumps, but
# might be useful for someone debugging some obscure memory issue
DEBUG_SHOW_MEMORY_ACTIONS = False

# TODO: remove the driver version when it's in mainline chirp
DRIVER_VERSION = "Quansheng UV-K5/K6/5R driver v20231218 (c) egzumer"
VALEUR_COMPILER = "ENABLE"

MEM_FORMAT = """
//#seekto 0x0000;
struct {
  ul32 freq;
  ul32 offset;

// 0x08
  u8 rxcode;
  u8 txcode;

// 0x0A
  u8 unknown1:2,
  txcodeflag:2,
  unknown2:2,
  rxcodeflag:2;

// 0x0B
  u8 modulation:4,
  __UNUSED:2,
  shift:2;

// 0x0C
  u8 __UNUSED1:3,
  busyChLockout:1,
  txpower:2,
  bandwidth:1,
  freq_reverse:1;

  // 0x0D
  u8 __UNUSED2:4,
  dtmf_pttid:3,
  dtmf_decode:1;

  // 0x0E
  u8 step;
  u8 scrambler;

} channel[214];

//#seekto 0xd60;
struct {
u8 is_scanlist1:1,
is_scanlist2:1,
compander:2,
is_free:1,
band:3;
} channel_attributes[200];

#seekto 0xe40;
ul16 fmfreq[20];

#seekto 0xe70;
u8 call_channel;
u8 squelch;
u8 max_talk_time;
u8 noaa_autoscan;
u8 key_lock;
u8 vox_switch;
u8 vox_level;
u8 mic_gain;

struct {
  u8 backlight_min:4,
  backlight_max:4;
  } backlight;
u8 channel_display_mode;
u8 crossband;
u8 battery_save;
u8 dual_watch;
u8 backlight_auto_mode;
u8 tail_note_elimination;
u8 vfo_open;

#seekto 0xe90;
struct {
  u8 keyM_longpress_action:7,
     button_beep:1;
  } _0xe90;
u8 key1_shortpress_action;
u8 key1_longpress_action;
u8 key2_shortpress_action;
u8 key2_longpress_action;
u8 scan_resume_mode;
u8 auto_keypad_lock;
u8 power_on_dispmode;
u8 password[4];

#seekto 0xea0;
u8 voice;
u8 S0_S_meter_level_dbm;
u8 S9_S_meter_level_dbm;

#seekto 0xea8;
u8 alarm_mode;
u8 reminding_of_end_talk_ROGER;
u8 repeater_tail_elimination;
u8 TX_VFO;
u8 Battery_type;

#seekto 0xeb0;
char logo_line1[16];
char logo_line2[16];

//#seekto 0xed0;
struct {
u8 side_tone;
char separate_code;
char group_call_code;
u8 decode_response;
u8 auto_reset_time;
u8 preload_time;
u8 first_code_persist_time;
u8 hash_persist_time;
u8 code_persist_time;
u8 code_interval_time;
u8 permit_remote_kill;
} dtmf_settings;

#seekto 0xee0;
struct {
char dtmf_local_code[3];
char unused1[5];
char kill_code[5];
char unused2[3];
char revive_code[5];
char unused3[3];
char dtmf_up_code[16];
char dtmf_down_code[16];
} dtmf_settings_numbers;

//#seekto 0xf18;
u8 scanlist_default;
u8 scanlist1_priority_scan;
u8 scanlist1_priority_ch1;
u8 scanlist1_priority_ch2;
u8 scanlist2_priority_scan;
u8 scanlist2_priority_ch1;
u8 scanlist2_priority_ch2;
u8 scanlist_unknown_0xff;


#seekto 0xf40;
u8 int_flock;
u8 int_350tx;
u8 int_KILLED;
u8 int_200tx;
u8 int_500tx;
u8 int_350en;
u8 int_scren;

struct {
u8  Setting_backlight_on_TX_RX:2,
    Setting_AM_fix:1,
    Setting_mic_bar:1,
    Setting_battery_text:2,
    Setting_live_DTMF_decoder:1,
    unknown:1;
  } Multi_option;
  
#seekto 0xf50;
struct {
char name[16];
} channelname[200];

#seekto 0x1c00;
struct {
char name[8];
char number[3];
char unused_00[5];
} dtmfcontact[16];

#seekto 0x1FF0;
struct {
u8 ENABLE_DTMF_CALLING:1,
   ENABLE_PWRON_PASSWORD:1,
   ENABLE_TX1750:1,
   ENABLE_ALARM:1,
   ENABLE_VOX:1,
   ENABLE_VOICE:1,
   ENABLE_NOAA:1,
   ENABLE_FMRADIO:1;
u8 __UNUSED:3,
   ENABLE_AM_FIX:1,
   ENABLE_BLMIN_TMP_OFF:1,
   ENABLE_RAW_DEMODULATORS:1,
   ENABLE_WIDE_RX:1,
   ENABLE_FLASHLIGHT:1;
} BUILD_OPTIONS;

"""
# bits that we will save from the channel structure (mostly unknown)
SAVE_MASK_0A = 0b11001100
SAVE_MASK_0B = 0b00001100
SAVE_MASK_0C = 0b11100000
SAVE_MASK_0D = 0b11110000

# flags1
FLAGS1_OFFSET_NONE = 0b00
FLAGS1_OFFSET_MINUS = 0b10
FLAGS1_OFFSET_PLUS = 0b01

POWER_HIGH = 0b10
POWER_MEDIUM = 0b01
POWER_LOW = 0b00

# dtmf_flags
PTTID_LIST = ["OFF", "UP CODE", "DOWN CODE", "UP+DOWN CODE", "APOLLO QUINDAR"]

# power
UVK5_POWER_LEVELS = [chirp_common.PowerLevel("Low",  watts=1.50),
                     chirp_common.PowerLevel("Med",  watts=3.00),
                     chirp_common.PowerLevel("High", watts=5.00),
                     ]

# scrambler
SCRAMBLER_LIST = ["OFF", "2600Hz", "2700", "2800Hz", "2900Hz", "3000Hz",
                   "3100Hz", "3200Hz", "3300Hz", "3400Hz", "3500Hz"]
# compander
COMPANDER_LIST = ["OFF", "TX", "RX", "TX/RX"]
# rx mode
RXMODE_LIST = ["MAIN ONLY", "DUAL RX RESPOND", "CROSS BAND", "MAIN TX DUAL RX"]
# channel display mode
CHANNELDISP_LIST = ["Frequency", "Channel Number", "Name", "Name + Freqency"]

# battery save
BATSAVE_LIST = ["OFF", "1:1", "1:2", "1:3", "1:4"]

# battery type
BATTYPE_LIST = ["1600 mAh", "2200 mAh"]
# bat txt
BAT_TXT_LIST = ["NONE", "VOLTAGE", "PERCENT"]
# Backlight auto mode
BACKLIGHT_LIST = ["OFF", "5s", "10s", "20s", "1min", "2min", "4min",
                  "Always On"]

# Backlight LVL
BACKLIGHT_LVL_LIST = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

# Backlight _TX_RX_LIST
BACKLIGHT_TX_RX_LIST = ["OFF", "TX", "RX", "TX/RX"]

# steps TODO: change order
STEPS = [2.5, 5, 6.25, 10, 12.5, 25, 8.33, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 1.25,
         9, 15, 20, 30, 50, 100, 125, 200, 250, 500]

# ctcss/dcs codes
TMODES = ["", "Tone", "DTCS", "DTCS"]
TONE_NONE = 0
TONE_CTCSS = 1
TONE_DCS = 2
TONE_RDCS = 3


CTCSS_TONES = [
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4,
    88.5, 91.5, 94.8, 97.4, 100.0, 103.5, 107.2, 110.9,
    114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2,
    151.4, 156.7, 159.8, 162.2, 165.5, 167.9, 171.3, 173.8,
    177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6, 199.5,
    203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8,
    250.3, 254.1
]

# lifted from ft4.py
DTCS_CODES = [ # TODO: add negative codes
    23,  25,  26,  31,  32,  36,  43,  47,  51,  53,  54,
    65,  71,  72,  73,  74,  114, 115, 116, 122, 125, 131,
    132, 134, 143, 145, 152, 155, 156, 162, 165, 172, 174,
    205, 212, 223, 225, 226, 243, 244, 245, 246, 251, 252,
    255, 261, 263, 265, 266, 271, 274, 306, 311, 315, 325,
    331, 332, 343, 346, 351, 356, 364, 365, 371, 411, 412,
    413, 423, 431, 432, 445, 446, 452, 454, 455, 462, 464,
    465, 466, 503, 506, 516, 523, 526, 532, 546, 565, 606,
    612, 624, 627, 631, 632, 654, 662, 664, 703, 712, 723,
    731, 732, 734, 743, 754
]

# flock list extended 
FLOCK_LIST = ["DEFAULT+ (137-174, 400-470 + Tx200, Tx350, Tx500)", 
              "FCC HAM (144-148, 420-450)", 
              "CE HAM (144-146, 430-440)", 
              "GB HAM (144-148, 430-440)", 
              "137-174, 400-430", 
              "137-174, 400-438", 
              "Disable All",
              "Unlock All"]

SCANRESUME_LIST = ["TO: Resume after 5 seconds (TIMEOUT)",
                   "CO: Resume after signal dissapears (CARRIER)",
                   "SE: Stop scanning after receiving a signal (STOP)"]
WELCOME_LIST = ["FULL", "MESSAGE", "VOLTAGE", "NONE"]
VOICE_LIST = ["OFF", "Chinese", "English"]

ALARMMODE_LIST = ["SITE", "TONE"]
REMENDOFTALK_LIST = ["OFF", "ROGER", "MDC"]
RTE_LIST = ["OFF", "100ms", "200ms", "300ms", "400ms",
            "500ms", "600ms", "700ms", "800ms", "900ms"]
VOX_LIST = ["OFF", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

MEM_SIZE = 0x2000  # size of all memory
PROG_SIZE = 0x1d00  # size of the memory that we will write
MEM_BLOCK = 0x80  # largest block of memory that we can reliably write

# fm radio supported frequencies
FMMIN = 76.0
FMMAX = 108.0

# bands supported by the UV-K5
BANDS_STANDARD = {
        0: [ 50.0, 76.0],
        1: [108.0, 135.9999],
        2: [136.0, 199.9990],
        3: [200.0, 299.9999],
        4: [350.0, 399.9999],
        5: [400.0, 469.9999],
        6: [470.0, 600.0]
        }

BANDS_WIDE = {
        0: [ 18.0, 108.0],
        1: [108.0, 135.9999],
        2: [136.0, 199.9990],
        3: [200.0, 299.9999],
        4: [350.0, 399.9999],
        5: [400.0, 469.9999],
        6: [470.0, 1300.0]
        }

SCANLIST_LIST = ["None", "List1", "List2", "Both"]
SCANLIST_SELECT_LIST = ["LIST1", "LIST2", "ALL"]

DTMF_CHARS = "0123456789ABCD*# "
DTMF_CHARS_ID = "0123456789ABCDabcd"
DTMF_CHARS_KILL = "0123456789ABCDabcd"
DTMF_CHARS_UPDOWN = "0123456789ABCDabcd#* "
DTMF_CODE_CHARS = "ABCD*# "
DTMF_DECODE_RESPONSE_LIST = ["None", "Ring", "Reply", "Both"]

KEYACTIONS_LIST = ["None",
                   "Flashlight",
                   "Power",
                   "Monitor",
                   "Scan",
                   "VOX",
                   "Alarm",
                   "FM radio",
                   "1750Hz tone",
                   "Lock keypad",
                   "Switch main VFO",
                   "Switch frequency/memory mode",
                   "Switch demodulation"
                   ]

# the communication is obfuscated using this fine mechanism
def xorarr(data: bytes):
    tbl = [22, 108, 20, 230, 46, 145, 13, 64, 33, 53, 213, 64, 19, 3, 233, 128]
    x = b""
    r = 0
    for byte in data:
        x += bytes([byte ^ tbl[r]])
        r = (r+1) % len(tbl)
    return x


# if this crc was used for communication to AND from the radio, then it
# would be a measure to increase reliability.
# but it's only used towards the radio, so it's for further obfuscation
def calculate_crc16_xmodem(data: bytes):
    poly = 0x1021
    crc = 0x0
    for byte in data:
        crc = crc ^ (byte << 8)
        for i in range(8):
            crc = crc << 1
            if (crc & 0x10000):
                crc = (crc ^ poly) & 0xFFFF
    return crc & 0xFFFF


def _send_command(serport, data: bytes):
    """Send a command to UV-K5 radio"""
    LOG.debug("Sending command (unobfuscated) len=0x%4.4x:\n%s" %
              (len(data), util.hexprint(data)))

    crc = calculate_crc16_xmodem(data)
    data2 = data + struct.pack("<H", crc)

    command = struct.pack(">HBB", 0xabcd, len(data), 0) + \
        xorarr(data2) + \
        struct.pack(">H", 0xdcba)
    if DEBUG_SHOW_OBFUSCATED_COMMANDS:
        LOG.debug("Sending command (obfuscated):\n%s" % util.hexprint(command))
    try:
        result = serport.write(command)
    except Exception:
        raise errors.RadioError("Error writing data to radio")
    return result


def _receive_reply(serport):
    header = serport.read(4)
    if len(header) != 4:
        LOG.warning("Header short read: [%s] len=%i" %
                    (util.hexprint(header), len(header)))
        raise errors.RadioError("Header short read")
    if header[0] != 0xAB or header[1] != 0xCD or header[3] != 0x00:
        LOG.warning("Bad response header: %s len=%i" %
                    (util.hexprint(header), len(header)))
        raise errors.RadioError("Bad response header")

    cmd = serport.read(int(header[2]))
    if len(cmd) != int(header[2]):
        LOG.warning("Body short read: [%s] len=%i" %
                    (util.hexprint(cmd), len(cmd)))
        raise errors.RadioError("Command body short read")

    footer = serport.read(4)

    if len(footer) != 4:
        LOG.warning("Footer short read: [%s] len=%i" %
                    (util.hexprint(footer), len(footer)))
        raise errors.RadioError("Footer short read")

    if footer[2] != 0xDC or footer[3] != 0xBA:
        LOG.debug(
                "Reply before bad response footer (obfuscated)"
                "len=0x%4.4x:\n%s" % (len(cmd), util.hexprint(cmd)))
        LOG.warning("Bad response footer: %s len=%i" %
                    (util.hexprint(footer), len(footer)))
        raise errors.RadioError("Bad response footer")

    if DEBUG_SHOW_OBFUSCATED_COMMANDS:
        LOG.debug("Received reply (obfuscated) len=0x%4.4x:\n%s" %
                  (len(cmd), util.hexprint(cmd)))

    cmd2 = xorarr(cmd)

    LOG.debug("Received reply (unobfuscated) len=0x%4.4x:\n%s" %
              (len(cmd2), util.hexprint(cmd2)))

    return cmd2


def _getstring(data: bytes, begin, maxlen):
    tmplen = min(maxlen+1, len(data))
    s = [data[i] for i in range(begin, tmplen)]
    for key, val in enumerate(s):
        if val < ord(' ') or val > ord('~'):
            break
    return ''.join(chr(x) for x in s[0:key])


def _sayhello(serport):
    hellopacket = b"\x14\x05\x04\x00\x6a\x39\x57\x64"

    tries = 5
    while True:
        LOG.debug("Sending hello packet")
        _send_command(serport, hellopacket)
        o = _receive_reply(serport)
        if (o):
            break
        tries -= 1
        if tries == 0:
            LOG.warning("Failed to initialise radio")
            raise errors.RadioError("Failed to initialize radio")
    firmware = _getstring(o, 4, 24)

    LOG.info("Found firmware: %s" % firmware)
    return firmware


def _readmem(serport, offset, length):
    LOG.debug("Sending readmem offset=0x%4.4x len=0x%4.4x" % (offset, length))

    readmem = b"\x1b\x05\x08\x00" + \
        struct.pack("<HBB", offset, length, 0) + \
        b"\x6a\x39\x57\x64"
    _send_command(serport, readmem)
    o = _receive_reply(serport)
    if DEBUG_SHOW_MEMORY_ACTIONS:
        LOG.debug("readmem Received data len=0x%4.4x:\n%s" %
                  (len(o), util.hexprint(o)))
    return o[8:]


def _writemem(serport, data, offset):
    LOG.debug("Sending writemem offset=0x%4.4x len=0x%4.4x" %
              (offset, len(data)))

    if DEBUG_SHOW_MEMORY_ACTIONS:
        LOG.debug("writemem sent data offset=0x%4.4x len=0x%4.4x:\n%s" %
                  (offset, len(data), util.hexprint(data)))

    dlen = len(data)
    writemem = b"\x1d\x05" + \
        struct.pack("<BBHBB", dlen+8, 0, offset, dlen, 1) + \
        b"\x6a\x39\x57\x64"+data

    _send_command(serport, writemem)
    o = _receive_reply(serport)

    LOG.debug("writemem Received data: %s len=%i" % (util.hexprint(o), len(o)))

    if (o[0] == 0x1e
            and
            o[4] == (offset & 0xff)
            and
            o[5] == (offset >> 8) & 0xff):
        return True
    else:
        LOG.warning("Bad data from writemem")
        raise errors.RadioError("Bad response to writemem")


def _resetradio(serport):
    resetpacket = b"\xdd\x05\x00\x00"
    _send_command(serport, resetpacket)


def do_download(radio):
    serport = radio.pipe
    serport.timeout = 0.5
    status = chirp_common.Status()
    status.cur = 0
    status.max = MEM_SIZE
    status.msg = "Downloading from radio"
    radio.status_fn(status)

    eeprom = b""
    f = _sayhello(serport)
    if f:
        radio.FIRMWARE_VERSION = f
    else:
        return False

    addr = 0
    while addr < MEM_SIZE:
        o = _readmem(serport, addr, MEM_BLOCK)
        status.cur = addr
        radio.status_fn(status)

        if o and len(o) == MEM_BLOCK:
            eeprom += o
            addr += MEM_BLOCK
        else:
            raise errors.RadioError("Memory download incomplete")

    return memmap.MemoryMapBytes(eeprom)


def do_upload(radio):
    serport = radio.pipe
    serport.timeout = 0.5
    status = chirp_common.Status()
    status.cur = 0
    status.max = PROG_SIZE
    status.msg = "Uploading to radio"
    radio.status_fn(status)

    f = _sayhello(serport)
    if f:
        radio.FIRMWARE_VERSION = f
    else:
        return False

    addr = 0
    while addr < PROG_SIZE:
        o = radio.get_mmap()[addr:addr+MEM_BLOCK]
        _writemem(serport, o, addr)
        status.cur = addr
        radio.status_fn(status)
        if o:
            addr += MEM_BLOCK
        else:
            raise errors.RadioError("Memory upload incomplete")
    status.msg = "Uploaded OK"

    _resetradio(serport)

    return True


def _find_band(self, hz):
    mhz = hz/1000000.0
    BANDS = BANDS_WIDE if self._memobj.BUILD_OPTIONS.ENABLE_WIDE_RX else BANDS_STANDARD
    for a in BANDS:
        if mhz >= BANDS[a][0] and mhz <= BANDS[a][1]:
            return a
    return False


@directory.register
class UVK5Radio(chirp_common.CloneModeRadio):
    """Quansheng UV-K5"""
    VENDOR = "Quansheng"
    MODEL = "UV-K5 (egzumer)"
    BAUD_RATE = 38400
    NEEDS_COMPAT_SERIAL = False
    FIRMWARE_VERSION = ""

    def Get_VFO_CHANNEL_NAMES(self):
        isWide = self._memobj.BUILD_OPTIONS.ENABLE_WIDE_RX
        BANDS = BANDS_STANDARD if not isWide else BANDS_WIDE
        names = []
        for b in range(7):
            name = "F{}({}M-{}M)".format(
                b + 1, 
                round(BANDS[b][0]),
                round(BANDS[b][1]))
            names.append(name + "A")
            names.append(name + "B")
        return names

    def Get_SPECIALS(self):
        specials = {}
        for idx, name in enumerate(self.Get_VFO_CHANNEL_NAMES()):
            specials[name] = 200 + idx
        return specials
    
    def get_prompts(x=None):
        rp = chirp_common.RadioPrompts()
        rp.experimental = \
            ('This is an experimental driver for the Quansheng UV-K5. '
             'It may harm your radio, or worse. Use at your own risk.\n\n'
             'Before attempting to do any changes please download'
             'the memory image from the radio with chirp '
             'and keep it. This can be later used to recover the '
             'original settings. \n\n'
             'some details are not yet implemented')
        rp.pre_download = _(
            "1. Turn radio on.\n"
            "2. Connect cable to mic/spkr connector.\n"
            "3. Make sure connector is firmly connected.\n"
            "4. Click OK to download image from device.\n\n"
            "It may not work if you turn on the radio "
            "with the cable already attached\n")
        rp.pre_upload = _(
            "1. Turn radio on.\n"
            "2. Connect cable to mic/spkr connector.\n"
            "3. Make sure connector is firmly connected.\n"
            "4. Click OK to upload the image to device.\n\n"
            "It may not work if you turn on the radio "
            "with the cable already attached")
        return rp

    # Return information about this radio's features, including
    # how many memories it has, what bands it supports, etc
    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_bank = False
        rf.valid_dtcs_codes = DTCS_CODES
        rf.has_rx_dtcs = True
        rf.has_ctone = True
        rf.has_settings = True
        rf.has_comment = False
        rf.valid_name_length = 10
        rf.valid_power_levels = UVK5_POWER_LEVELS
        rf.valid_special_chans = self.Get_VFO_CHANNEL_NAMES()

        rf.valid_tuning_steps = STEPS

        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = ["Tone->Tone", "Tone->DTCS", "DTCS->Tone",
                                "->Tone", "->DTCS", "DTCS->", "DTCS->DTCS"]

        rf.valid_characters = chirp_common.CHARSET_ASCII
        rf.valid_modes = ["FM", "NFM", "AM", "NAM", "USB"]

        rf.valid_skips = [""]

        # This radio supports memories 1-200, 201-214 are the VFO memories
        rf.memory_bounds = (1, 200)

        # This is what the BK4819 chip supports
        # Will leave it in a comment, might be useful someday
        # rf.valid_bands = [(18000000,  620000000),
        #                  (840000000, 1300000000)
        #                  ]
        rf.valid_bands = []
        BANDS = BANDS_WIDE if self._memobj.BUILD_OPTIONS.ENABLE_WIDE_RX else BANDS_STANDARD
        for a in BANDS:
            rf.valid_bands.append(
                    (int(BANDS[a][0]*1000000), int(BANDS[a][1]*1000000)))
        return rf

    # Do a download of the radio from the serial port
    def sync_in(self):
        self._mmap = do_download(self)
        self.process_mmap()

    # Do an upload of the radio to the serial port
    def sync_out(self):
        do_upload(self)

    # Convert the raw byte array into a memory object structure
    def process_mmap(self):
        self._memobj = bitwise.parse(MEM_FORMAT, self._mmap)

    # Return a raw representation of the memory object, which
    # is very helpful for development
    def get_raw_memory(self, number):
        return repr(self._memobj.channel[number-1])

    def validate_memory(self, mem):
        msgs = super().validate_memory(mem)

        # find tx frequency
        if mem.duplex == '-':
            txfreq = mem.freq - mem.offset
        elif mem.duplex == '+':
            txfreq = mem.freq + mem.offset
        else:
            txfreq = mem.freq

        # find band
        band = _find_band(self, txfreq)
        if band is False:
            msg = "Transmit frequency %.4fMHz is not supported by this radio" \
                   % (txfreq/1000000.0)
            msgs.append(chirp_common.ValidationWarning(msg))

        band = _find_band(self, mem.freq)
        if band is False:
            msg = "The frequency %.4fMHz is not supported by this radio" \
                   % (mem.freq/1000000.0)
            msgs.append(chirp_common.ValidationWarning(msg))

        return msgs

    def _set_tone(self, mem, _mem):
        ((txmode, txtone, txpol),
         (rxmode, rxtone, rxpol)) = chirp_common.split_tone_encode(mem)

        if txmode == "Tone":
            txtoval = CTCSS_TONES.index(txtone)
            txmoval = 0b01
        elif txmode == "DTCS":
            txmoval = txpol == "R" and 0b11 or 0b10
            txtoval = DTCS_CODES.index(txtone)
        else:
            txmoval = 0
            txtoval = 0

        if rxmode == "Tone":
            rxtoval = CTCSS_TONES.index(rxtone)
            rxmoval = 0b01
        elif rxmode == "DTCS":
            rxmoval = rxpol == "R" and 0b11 or 0b10
            rxtoval = DTCS_CODES.index(rxtone)
        else:
            rxmoval = 0
            rxtoval = 0

        _mem.rxcodeflag = rxmoval
        _mem.txcodeflag = txmoval
        _mem.unknown1 = 0
        _mem.unknown2 = 0
        _mem.rxcode = rxtoval
        _mem.txcode = txtoval

    def _get_tone(self, mem, _mem):
        rxtype = _mem.rxcodeflag
        txtype = _mem.txcodeflag
        rx_tmode = TMODES[rxtype]
        tx_tmode = TMODES[txtype]

        rx_tone = tx_tone = None

        if tx_tmode == "Tone":
            if _mem.txcode < len(CTCSS_TONES):
                tx_tone = CTCSS_TONES[_mem.txcode]
            else:
                tx_tone = 0
                tx_tmode = ""
        elif tx_tmode == "DTCS":
            if _mem.txcode < len(DTCS_CODES):
                tx_tone = DTCS_CODES[_mem.txcode]
            else:
                tx_tone = 0
                tx_tmode = ""

        if rx_tmode == "Tone":
            if _mem.rxcode < len(CTCSS_TONES):
                rx_tone = CTCSS_TONES[_mem.rxcode]
            else:
                rx_tone = 0
                rx_tmode = ""
        elif rx_tmode == "DTCS":
            if _mem.rxcode < len(DTCS_CODES):
                rx_tone = DTCS_CODES[_mem.rxcode]
            else:
                rx_tone = 0
                rx_tmode = ""

        tx_pol = txtype == 0x03 and "R" or "N"
        rx_pol = rxtype == 0x03 and "R" or "N"

        chirp_common.split_tone_decode(mem, (tx_tmode, tx_tone, tx_pol),
                                       (rx_tmode, rx_tone, rx_pol))

    # Extract a high-level memory object from the low-level memory map
    # This is called to populate a memory in the UI
    def get_memory(self, number2):

        mem = chirp_common.Memory()

        if isinstance(number2, str):
            number = self.Get_SPECIALS()[number2]
            mem.extd_number = number2
        else:
            number = number2 - 1

        mem.number = number + 1

        _mem = self._memobj.channel[number]

        tmpcomment = ""

        is_empty = False
        # We'll consider any blank (i.e. 0MHz frequency) to be empty
        if (_mem.freq == 0xffffffff) or (_mem.freq == 0):
            is_empty = True

        # We'll also look at the channel attributes if a memory has them
        tmpscn = SCANLIST_LIST[0]
        tmpComp = COMPANDER_LIST[0]
        if number < 200:
            _mem3 = self._memobj.channel_attributes[number]
            # free memory bit
            if _mem3.is_free:
                is_empty = True
            # scanlists
            tempVal = _mem3.is_scanlist1 + _mem3.is_scanlist2 * 2
            tmpscn = SCANLIST_LIST[tempVal]
            tmpComp = COMPANDER_LIST[_mem3.compander]

        if is_empty:
            mem.empty = True
            # set some sane defaults:
            mem.power = UVK5_POWER_LEVELS[2]
            mem.extra = RadioSettingGroup("Extra", "extra")
            rs = RadioSetting("busyChLockout", "BusyCL", RadioSettingValueBoolean(False))
            mem.extra.append(rs)

            rs = RadioSetting("frev", "FreqRev",
                              RadioSettingValueBoolean(False))
            mem.extra.append(rs)

            rs = RadioSetting("pttid", "PTTID", RadioSettingValueList(
                PTTID_LIST, PTTID_LIST[0]))
            mem.extra.append(rs)

            rs = RadioSetting("dtmfdecode", "DTMF decode",
                              RadioSettingValueBoolean(False))
            if self._memobj.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
                mem.extra.append(rs)

            rs = RadioSetting("scrambler", "Scrambler", RadioSettingValueList(
                SCRAMBLER_LIST, SCRAMBLER_LIST[0]))
            mem.extra.append(rs)

            rs = RadioSetting("compander", "Compander", RadioSettingValueList(
                COMPANDER_LIST, COMPANDER_LIST[0]))
            mem.extra.append(rs)

            rs = RadioSetting("scanlists", "Scanlists", RadioSettingValueList(
                SCANLIST_LIST, SCANLIST_LIST[0]))
            mem.extra.append(rs)

            # actually the step and duplex are overwritten by chirp based on
            # bandplan. they are here to document sane defaults for IARU r1
            # mem.tuning_step = 25.0
            # mem.duplex = "OFF"

            return mem

        if number > 199:
            mem.name = self.Get_VFO_CHANNEL_NAMES()[number-200]
            mem.immutable = ["name", "scanlists"]
        else:
            _mem2 = self._memobj.channelname[number]
            for char in _mem2.name:
                if str(char) == "\xFF" or str(char) == "\x00":
                    break
                mem.name += str(char)
            mem.name = mem.name.rstrip()

        # Convert your low-level frequency to Hertz
        mem.freq = int(_mem.freq)*10
        mem.offset = int(_mem.offset)*10

        if (mem.offset == 0):
            mem.duplex = ''
        else:
            if _mem.shift == FLAGS1_OFFSET_MINUS:
                mem.duplex = '-'
            elif _mem.shift == FLAGS1_OFFSET_PLUS:
                mem.duplex = '+'
            else:
                mem.duplex = ''

        # tone data
        self._get_tone(mem, _mem)

        # mode
        tempModes = self.get_features().valid_modes
        tempModul = _mem.modulation*2 + _mem.bandwidth
        if tempModul < len(tempModes):
            mem.mode = tempModes[tempModul]
        elif tempModul == 5: # USB with narrow setting
            mem.mode = tempModes[4]
        elif tempModul >= len(tempModes):
            mem.mode = "UNSUPPORTED BY CHIRP"
        
        # tuning step
        tstep = _mem.step & 0x7
        if tstep < len(STEPS):
            mem.tuning_step = STEPS[tstep]
        else:
            mem.tuning_step = 2.5

        # power
        if _mem.txpower == POWER_HIGH:
            mem.power = UVK5_POWER_LEVELS[2]
        elif _mem.txpower == POWER_MEDIUM:
            mem.power = UVK5_POWER_LEVELS[1]
        else:
            mem.power = UVK5_POWER_LEVELS[0]

        # We'll consider any blank (i.e. 0MHz frequency) to be empty
        if (_mem.freq == 0xffffffff) or (_mem.freq == 0):
            mem.empty = True
        else:
            mem.empty = False

        mem.extra = RadioSettingGroup("Extra", "extra")

        # BusyCL
        is_bclo = bool(_mem.busyChLockout)
        rs = RadioSetting("busyChLockout", "Busy Ch Lockout", RadioSettingValueBoolean(is_bclo))
        mem.extra.append(rs)
        tmpcomment += "BusyCL:"+(is_bclo and "ON" or "OFF")+" "

        # Frequency reverse - whatever that means, don't see it in the manual
        is_frev = bool(_mem.freq_reverse > 0)
        rs = RadioSetting("frev", "Reverse Frequencies", RadioSettingValueBoolean(is_frev))
        mem.extra.append(rs)
        tmpcomment += "FreqReverse:"+(is_frev and "ON" or "OFF")+" "

        # PTTID
        pttid = _mem.dtmf_pttid
        rs = RadioSetting("pttid", "PTT ID", RadioSettingValueList(
            PTTID_LIST, PTTID_LIST[pttid]))
        mem.extra.append(rs)
        tmpcomment += "PTTid:"+PTTID_LIST[pttid]+" "

        # DTMF DECODE
        is_dtmf = bool(_mem.dtmf_decode > 0)
        rs = RadioSetting("dtmfdecode", "DTMF decode",
                          RadioSettingValueBoolean(is_dtmf))
        mem.extra.append(rs)
        tmpcomment += "DTMFdecode:"+(is_dtmf and "ON" or "OFF") + " "

        # Scrambler
        enc = _mem.scrambler if _mem.scrambler < len(SCRAMBLER_LIST) else 0
        rs = RadioSetting("scrambler", "Scrambler (Scramb)", RadioSettingValueList(
            SCRAMBLER_LIST, SCRAMBLER_LIST[enc]))
        mem.extra.append(rs)
        tmpcomment += "Scrambler:" + SCRAMBLER_LIST[enc] + " "

        # Compander
        rs = RadioSetting("compander", "Compander (Compnd)", RadioSettingValueList(
            COMPANDER_LIST, tmpComp))
        mem.extra.append(rs)
        tmpcomment += "Compander:" + tmpComp + " "

        rs = RadioSetting("scanlists", "Scanlists (SList)", RadioSettingValueList(
            SCANLIST_LIST, tmpscn))
        mem.extra.append(rs)

        return mem

    def set_settings(self, settings):
        _mem = self._memobj
        for element in settings:
            if not isinstance(element, RadioSetting):
                self.set_settings(element)
                continue

            # basic settings

            # call channel
            if element.get_name() == "call_channel":
                _mem.call_channel = int(element.value)-1

            # squelch
            if element.get_name() == "squelch":
                _mem.squelch = int(element.value)
            # TOT
            if element.get_name() == "tot":
                _mem.max_talk_time = int(element.value)

            # NOAA autoscan
            if element.get_name() == "noaa_autoscan":
                _mem.noaa_autoscan = element.value and 1 or 0

            # VOX
            if element.get_name() == "vox":
                voxvalue = VOX_LIST.index(str(element.value))
                _mem.vox_switch = voxvalue > 0
                _mem.vox_level = (voxvalue - 1) if _mem.vox_switch else 0

            # mic gain
            if element.get_name() == "mic_gain":
                _mem.mic_gain = int(element.value)

            # Channel display mode
            if element.get_name() == "channel_display_mode":
                _mem.channel_display_mode = CHANNELDISP_LIST.index(
                    str(element.value))

            # RX Mode
            if element.get_name() == "rx_mode":
                tmptxmode = RXMODE_LIST.index(str(element.value))
                tmpmainvfo = _mem.TX_VFO + 1
                _mem.crossband = tmpmainvfo * bool(tmptxmode & 0b10)
                _mem.dual_watch = tmpmainvfo * bool(tmptxmode & 0b01)  

            # Battery Save
            if element.get_name() == "battery_save":
                _mem.battery_save = BATSAVE_LIST.index(str(element.value))


            # RX_MODE
            if element.get_name() == "RXMODE":
                tmprxmode = RXMODE_LIST.index(str(element.value))

            # Backlight auto mode
            if element.get_name() == "backlight_auto_mode":
                _mem.backlight_auto_mode = \
                        BACKLIGHT_LIST.index(str(element.value))

            # Backlight min
            if element.get_name() == "backlight.backlight_min":
                _mem.backlight.backlight_min = \
                        BACKLIGHT_LVL_LIST.index(str(element.value))

            # Backlight max
            if element.get_name() == "backlight.backlight_max":
                _mem.backlight.backlight_max = \
                        BACKLIGHT_LVL_LIST.index(str(element.value))

            # Backlight TX_RX
            if element.get_name() == "Multi_option.Setting_backlight_on_TX_RX":
                _mem.Multi_option.Setting_backlight_on_TX_RX = \
                        BACKLIGHT_TX_RX_LIST.index(str(element.value))  
                       
            # AM_fix
            if element.get_name() == "Multi_option.Setting_AM_fix":
                _mem.Multi_option.Setting_AM_fix = element.value and 1 or 0
                                          
            # mic_bar
            if element.get_name() == "mem.Multi_option.Setting_mic_bar":
                _mem.Multi_option.Setting_mic_bar = element.value and 1 or 0
                    
             # Batterie txt
            if element.get_name() == "_mem.Multi_option.Setting_battery_text":
                _mem.Multi_option.Setting_battery_text = \
                        BAT_TXT_LIST.index(str(element.value))  
                            
            # Tail tone elimination
            if element.get_name() == "tail_note_elimination":
                _mem.tail_note_elimination = element.value and 1 or 0

            # VFO Open
            if element.get_name() == "vfo_open":
                _mem.vfo_open = element.value and 1 or 0

             # Beep control
            if element.get_name() == "button_beep":
                _mem._0xe90.button_beep = element.value and 1 or 0 

            # Scan resume mode
            if element.get_name() == "scan_resume_mode":
                _mem.scan_resume_mode = SCANRESUME_LIST.index(
                    str(element.value))

            # Keypad lock
            if element.get_name() == "key_lock":
                _mem.key_lock = element.value and 1 or 0

            # Auto keypad lock
            if element.get_name() == "auto_keypad_lock":
                _mem.auto_keypad_lock = element.value and 1 or 0

            # Power on display mode
            if element.get_name() == "welcome_mode":
                _mem.power_on_dispmode = WELCOME_LIST.index(str(element.value))

            # Keypad Tone
            if element.get_name() == "voice":
                _mem.voice = VOICE_LIST.index(str(element.value))

            if element.get_name() == "S0_S_meter_level_dbm":
                _mem.S0_S_meter_level_dbm = -int(element.value)

            if element.get_name() == "S9_S_meter_level_dbm":
                _mem.S9_S_meter_level_dbm = -int(element.value)
            # Alarm mode
            if element.get_name() == "alarm_mode":
                _mem.alarm_mode = ALARMMODE_LIST.index(str(element.value))

            # Reminding of end of talk
            if element.get_name() == "reminding_of_end_talk_ROGER":
                _mem.reminding_of_end_talk_ROGER = REMENDOFTALK_LIST.index(
                    str(element.value))

            # Repeater tail tone elimination
            if element.get_name() == "repeater_tail_elimination":
                _mem.repeater_tail_elimination = RTE_LIST.index(
                    str(element.value))

            # Logo string 1
            if element.get_name() == "logo1":
                b = str(element.value).rstrip("\x20\xff\x00")+"\x00"*12
                _mem.logo_line1 = b[0:12]+"\x00\xff\xff\xff"

            # Logo string 2
            if element.get_name() == "logo2":
                b = str(element.value).rstrip("\x20\xff\x00")+"\x00"*12
                _mem.logo_line2 = b[0:12]+"\x00\xff\xff\xff"

            # unlock settings

            # FLOCK
            if element.get_name() == "int_flock":
                _mem.int_flock = FLOCK_LIST.index(str(element.value))

            # 350TX
            if element.get_name() == "int_350tx":
                _mem.int_350tx = element.value and 1 or 0

            # KILLED
            if element.get_name() == "int_KILLED":
                _mem.int_KILLED = element.value and 1 or 0

            # 200TX
            if element.get_name() == "int_200tx":
                _mem.int_200tx = element.value and 1 or 0

            # 500TX
            if element.get_name() == "int_500tx":
                _mem.int_500tx = element.value and 1 or 0

            # 350EN
            if element.get_name() == "int_350en":
                _mem.int_350en = element.value and 1 or 0

            # SCREN
            if element.get_name() == "int_scren":
                _mem.int_scren = element.value and 1 or 0

            # battery type
            if element.get_name() == "Battery_type":
                _mem.Battery_type = BATTYPE_LIST.index(str(element.value))
            # fm radio
            for i in range(1, 21):
                freqname = "FM_" + str(i)
                if element.get_name() == freqname:
                    val = str(element.value).strip()
                    try:
                        val2 = int(float(val)*10)
                    except Exception:
                        val2 = 0xffff

                    if val2 < FMMIN*10 or val2 > FMMAX*10:
                        val2 = 0xffff
#                        raise errors.InvalidValueError(
#                                "FM radio frequency should be a value "
#                                "in the range %.1f - %.1f" % (FMMIN , FMMAX))
                    _mem.fmfreq[i-1] = val2

            # dtmf settings
            if element.get_name() == "dtmf_side_tone":
                _mem.dtmf_settings.side_tone = \
                        element.value and 1 or 0

            if element.get_name() == "dtmf_separate_code":
                _mem.dtmf_settings.separate_code = str(element.value)

            if element.get_name() == "dtmf_group_call_code":
                _mem.dtmf_settings.group_call_code = element.value

            if element.get_name() == "dtmf_decode_response":
                _mem.dtmf_settings.decode_response = \
                        DTMF_DECODE_RESPONSE_LIST.index(str(element.value))

            if element.get_name() == "dtmf_auto_reset_time":
                _mem.dtmf_settings.auto_reset_time = \
                        int(int(element.value)/10)

            if element.get_name() == "dtmf_preload_time":
                _mem.dtmf_settings.preload_time = \
                        int(int(element.value)/10)

            if element.get_name() == "dtmf_first_code_persist_time":
                _mem.dtmf_settings.first_code_persist_time = \
                        int(int(element.value)/10)

            if element.get_name() == "dtmf_hash_persist_time":
                _mem.dtmf_settings.hash_persist_time = \
                        int(int(element.value)/10)

            if element.get_name() == "dtmf_code_persist_time":
                _mem.dtmf_settings.code_persist_time = \
                        int(int(element.value)/10)

            if element.get_name() == "dtmf_code_interval_time":
                _mem.dtmf_settings.code_interval_time = \
                        int(int(element.value)/10)

            if element.get_name() == "dtmf_permit_remote_kill":
                _mem.dtmf_settings.permit_remote_kill = \
                        element.value and 1 or 0

            if element.get_name() == "dtmf_dtmf_local_code":
                k = str(element.value).rstrip("\x20\xff\x00") + "\x00"*3
                _mem.dtmf_settings_numbers.dtmf_local_code = k[0:3]

            if element.get_name() == "dtmf_dtmf_up_code":
                k = str(element.value).strip("\x20\xff\x00") + "\x00"*16
                _mem.dtmf_settings_numbers.dtmf_up_code = k[0:16]

            if element.get_name() == "dtmf_dtmf_down_code":
                k = str(element.value).rstrip("\x20\xff\x00") + "\x00"*16
                _mem.dtmf_settings_numbers.dtmf_down_code = k[0:16]

            if element.get_name() == "dtmf_kill_code":
                k = str(element.value).strip("\x20\xff\x00") + "\x00"*5
                _mem.dtmf_settings_numbers.kill_code = k[0:5]

            if element.get_name() == "dtmf_revive_code":
                k = str(element.value).strip("\x20\xff\x00") + "\x00"*5
                _mem.dtmf_settings_numbers.revive_code = k[0:5]

            # dtmf contacts
            for i in range(1, 17):
                varname = "DTMF_" + str(i)
                if element.get_name() == varname:
                    k = str(element.value).rstrip("\x20\xff\x00") + "\x00"*8
                    _mem.dtmfcontact[i-1].name = k[0:8]

                varnumname = "DTMFNUM_" + str(i)
                if element.get_name() == varnumname:
                    k = str(element.value).rstrip("\x20\xff\x00") + "\xff"*3
                    _mem.dtmfcontact[i-1].number = k[0:3]

            # scanlist stuff
            if element.get_name() == "scanlist_default":
                _mem.scanlist_default = SCANLIST_SELECT_LIST.index(
                        str(element.value))

            if element.get_name() == "scanlist1_priority_scan":
                _mem.scanlist1_priority_scan = \
                        element.value and 1 or 0

            if element.get_name() == "scanlist2_priority_scan":
                _mem.scanlist2_priority_scan = \
                        element.value and 1 or 0

            if element.get_name() == "scanlist1_priority_ch1" or \
                    element.get_name() == "scanlist1_priority_ch2" or \
                    element.get_name() == "scanlist2_priority_ch1" or \
                    element.get_name() == "scanlist2_priority_ch2":

                val = int(element.value)

                if val > 200 or val < 1:
                    val = 0xff
                else:
                    val -= 1

                if element.get_name() == "scanlist1_priority_ch1":
                    _mem.scanlist1_priority_ch1 = val
                if element.get_name() == "scanlist1_priority_ch2":
                    _mem.scanlist1_priority_ch2 = val
                if element.get_name() == "scanlist2_priority_ch1":
                    _mem.scanlist2_priority_ch1 = val
                if element.get_name() == "scanlist2_priority_ch2":
                    _mem.scanlist2_priority_ch2 = val

            if element.get_name() == "key1_shortpress_action":
                _mem.key1_shortpress_action = KEYACTIONS_LIST.index(
                        str(element.value))

            if element.get_name() == "key1_longpress_action":
                _mem.key1_longpress_action = KEYACTIONS_LIST.index(
                        str(element.value))

            if element.get_name() == "key2_shortpress_action":
                _mem.key2_shortpress_action = KEYACTIONS_LIST.index(
                        str(element.value))

            if element.get_name() == "key2_longpress_action":
                _mem.key2_longpress_action = KEYACTIONS_LIST.index(
                        str(element.value))
                      
            if element.get_name() == "keyM_longpress_action":
                _mem._0xe90.keyM_longpress_action = KEYACTIONS_LIST.index(
                        str(element.value))

    def get_settings(self):
        _mem = self._memobj
        basic = RadioSettingGroup("basic", "Basic Settings")
        keya = RadioSettingGroup("keya", "Programmable keys")
        dtmf = RadioSettingGroup("dtmf", "DTMF Settings")
        dtmfc = RadioSettingGroup("dtmfc", "DTMF Contacts")
        scanl = RadioSettingGroup("scn", "Scan Lists")
        unlock = RadioSettingGroup("unlock", "Unlock Settings")
        fmradio = RadioSettingGroup("fmradio", "FM Radio")

        roinfo = RadioSettingGroup("roinfo", "Driver information")
        top = RadioSettings()
        top.append(basic)
        top.append(keya)
        top.append(dtmf)
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            top.append(dtmfc)
        top.append(scanl)
        top.append(unlock)
        if _mem.BUILD_OPTIONS.ENABLE_FMRADIO:
            top.append(fmradio)
        top.append(roinfo)

        # Programmable keys
        def GetActualKeyAction(actionNum):
            hasAlarm = self._memobj.BUILD_OPTIONS.ENABLE_ALARM
            has1750 = self._memobj.BUILD_OPTIONS.ENABLE_TX1750
            lst = KEYACTIONS_LIST.copy()
            if not hasAlarm:
                lst.remove("Alarm")
            if not has1750:
                lst.remove("1750Hz tone")

            actionNum = int(actionNum)
            if actionNum >= len(KEYACTIONS_LIST) or KEYACTIONS_LIST[actionNum] not in lst:
                actionNum = 0
            return lst, KEYACTIONS_LIST[actionNum]
        
        rs = RadioSetting("key1_shortpress_action", 
                          "Side key 1 short press (F1Shrt)",
                          RadioSettingValueList(
                              *GetActualKeyAction(_mem.key1_shortpress_action)))
        keya.append(rs)

        rs = RadioSetting("key1_longpress_action", "Side key 1 long press (F1Long)",
                          RadioSettingValueList(
                              *GetActualKeyAction(_mem.key1_longpress_action)))
        keya.append(rs)

        rs = RadioSetting("key2_shortpress_action", "Side key 2 short press (F2Shrt)",
                          RadioSettingValueList(
                              *GetActualKeyAction(_mem.key2_shortpress_action)))
        keya.append(rs)

        rs = RadioSetting("key2_longpress_action", "Side key 2 long press (F2Long)",
                          RadioSettingValueList(
                              *GetActualKeyAction(_mem.key2_longpress_action)))
        keya.append(rs)

        rs = RadioSetting("keyM_longpress_action", "Menu key long press (M Long)",
                          RadioSettingValueList(
                              *GetActualKeyAction(_mem._0xe90.keyM_longpress_action)))
        keya.append(rs)

        # DTMF settings
        tmppr = bool(_mem.dtmf_settings.side_tone > 0)
        rs = RadioSetting(
                "dtmf_side_tone",
                "DTMF Sidetone",
                RadioSettingValueBoolean(tmppr))
        dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings.separate_code)
        if tmpval not in DTMF_CODE_CHARS:
            tmpval = '*'
        val = RadioSettingValueString(1, 1, tmpval)
        val.set_charset(DTMF_CODE_CHARS)
        rs = RadioSetting("dtmf_separate_code", "Separate Code", val)
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings.group_call_code)
        if tmpval not in DTMF_CODE_CHARS:
            tmpval = '#'
        val = RadioSettingValueString(1, 1, tmpval)
        val.set_charset(DTMF_CODE_CHARS)
        rs = RadioSetting("dtmf_group_call_code", "Group Call Code", val)
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = _mem.dtmf_settings.decode_response
        if tmpval >= len(DTMF_DECODE_RESPONSE_LIST):
            tmpval = 0
        rs = RadioSetting("dtmf_decode_response", "Decode Response",
                          RadioSettingValueList(
                              DTMF_DECODE_RESPONSE_LIST,
                              DTMF_DECODE_RESPONSE_LIST[tmpval]))
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = _mem.dtmf_settings.auto_reset_time
        if tmpval > 60 or tmpval < 5:
            tmpval = 5
        rs = RadioSetting("dtmf_auto_reset_time",
                          "Auto reset time (s)",
                          RadioSettingValueInteger(5, 60, tmpval))
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = int(_mem.dtmf_settings.preload_time)
        if tmpval > 100 or tmpval < 3:
            tmpval = 30
        tmpval *= 10
        rs = RadioSetting("dtmf_preload_time",
                          "Pre-load time (ms)",
                          RadioSettingValueInteger(30, 1000, tmpval, 10))
        dtmf.append(rs)

        tmpval = int(_mem.dtmf_settings.first_code_persist_time)
        if tmpval > 100 or tmpval < 3:
            tmpval = 30
        tmpval *= 10
        rs = RadioSetting("dtmf_first_code_persist_time",
                          "First code persist time (ms)",
                          RadioSettingValueInteger(30, 1000, tmpval, 10))
        dtmf.append(rs)

        tmpval = int(_mem.dtmf_settings.hash_persist_time)
        if tmpval > 100 or tmpval < 3:
            tmpval = 30
        tmpval *= 10
        rs = RadioSetting("dtmf_hash_persist_time",
                          "#/* persist time (ms)",
                          RadioSettingValueInteger(30, 1000, tmpval, 10))
        dtmf.append(rs)

        tmpval = int(_mem.dtmf_settings.code_persist_time)
        if tmpval > 100 or tmpval < 3:
            tmpval = 30
        tmpval *= 10
        rs = RadioSetting("dtmf_code_persist_time",
                          "Code persist time (ms)",
                          RadioSettingValueInteger(30, 1000, tmpval, 10))
        dtmf.append(rs)

        tmpval = int(_mem.dtmf_settings.code_interval_time)
        if tmpval > 100 or tmpval < 3:
            tmpval = 30
        tmpval *= 10
        rs = RadioSetting("dtmf_code_interval_time",
                          "Code interval time (ms)",
                          RadioSettingValueInteger(30, 1000, tmpval, 10))
        dtmf.append(rs)

        tmpval = bool(_mem.dtmf_settings.permit_remote_kill > 0)
        rs = RadioSetting(
                "dtmf_permit_remote_kill",
                "Permit remote kill",
                RadioSettingValueBoolean(tmpval))
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings_numbers.dtmf_local_code).upper().strip(
                "\x00\xff\x20")
        for i in tmpval:
            if i in DTMF_CHARS_ID:
                continue
            else:
                tmpval = "103"
                break
        val = RadioSettingValueString(3, 3, tmpval)
        val.set_charset(DTMF_CHARS_ID)
        rs = RadioSetting("dtmf_dtmf_local_code",
                          "Local code (3 chars 0-9 ABCD)", val)
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings_numbers.dtmf_up_code).upper().strip(
                "\x00\xff\x20")
        for i in tmpval:
            if i in DTMF_CHARS_UPDOWN or i == "":
                continue
            else:
                tmpval = "123"
                break
        val = RadioSettingValueString(1, 16, tmpval)
        val.set_charset(DTMF_CHARS_UPDOWN)
        rs = RadioSetting("dtmf_dtmf_up_code",
                          "Up code (1-16 chars 0-9 ABCD*#)", val)
        dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings_numbers.dtmf_down_code).upper().strip(
                "\x00\xff\x20")
        for i in tmpval:
            if i in DTMF_CHARS_UPDOWN:
                continue
            else:
                tmpval = "456"
                break
        val = RadioSettingValueString(1, 16, tmpval)
        val.set_charset(DTMF_CHARS_UPDOWN)
        rs = RadioSetting("dtmf_dtmf_down_code",
                          "Down code (1-16 chars 0-9 ABCD*#)", val)
        dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings_numbers.kill_code).upper().strip(
                "\x00\xff\x20")
        for i in tmpval:
            if i in DTMF_CHARS_KILL:
                continue
            else:
                tmpval = "77777"
                break
        if not len(tmpval) == 5:
            tmpval = "77777"
        val = RadioSettingValueString(5, 5, tmpval)
        val.set_charset(DTMF_CHARS_KILL)
        rs = RadioSetting("dtmf_kill_code",
                          "Kill code (5 chars 0-9 ABCD)", val)
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        tmpval = str(_mem.dtmf_settings_numbers.revive_code).upper().strip(
                "\x00\xff\x20")
        for i in tmpval:
            if i in DTMF_CHARS_KILL:
                continue
            else:
                tmpval = "88888"
                break
        if not len(tmpval) == 5:
            tmpval = "88888"
        val = RadioSettingValueString(5, 5, tmpval)
        val.set_charset(DTMF_CHARS_KILL)
        rs = RadioSetting("dtmf_revive_code",
                          "Revive code (5 chars 0-9 ABCD)", val)
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        # Killed
        rs = RadioSetting("int_KILLED", "DTMF kill lock",
                          RadioSettingValueBoolean(
                              bool(_mem.int_KILLED > 0)))
        if _mem.BUILD_OPTIONS.ENABLE_DTMF_CALLING:
            dtmf.append(rs)

        val = RadioSettingValueString(0, 80,
                                      "All DTMF Contacts are 3 codes "
                                      "(valid: 0-9 * # ABCD), "
                                      "or an empty string")
        val.set_mutable(False)
        rs = RadioSetting("dtmf_descr1", "DTMF Contacts", val)
        dtmfc.append(rs)

        for i in range(1, 17):
            varname = "DTMF_"+str(i)
            varnumname = "DTMFNUM_"+str(i)
            vardescr = "DTMF Contact "+str(i)+" name"
            varinumdescr = "DTMF Contact "+str(i)+" number"

            cntn = str(_mem.dtmfcontact[i-1].name).strip("\x20\x00\xff")
            cntnum = str(_mem.dtmfcontact[i-1].number).strip("\x20\x00\xff")

            val = RadioSettingValueString(0, 8, cntn)
            rs = RadioSetting(varname, vardescr, val)
            dtmfc.append(rs)

            val = RadioSettingValueString(0, 3, cntnum)
            val.set_charset(DTMF_CHARS)
            rs = RadioSetting(varnumname, varinumdescr, val)
            dtmfc.append(rs)

        tmpscanl = _mem.scanlist_default
        rs = RadioSetting("scanlist_default",
                          "Default scanlist (SList)",
                          RadioSettingValueList(
                                SCANLIST_SELECT_LIST,
                                SCANLIST_SELECT_LIST[tmpscanl]))    
        scanl.append(rs)

        tmppr = bool((_mem.scanlist1_priority_scan & 1) > 0)
        rs = RadioSetting(
                "scanlist1_priority_scan",
                "Scanlist 1 priority channel scan",
                RadioSettingValueBoolean(tmppr))
        scanl.append(rs)

        tmpch = _mem.scanlist1_priority_ch1 + 1
        if tmpch > 200:
            tmpch = 0
        rs = RadioSetting("scanlist1_priority_ch1",
                          "Scanlist 1 priority channel 1 (0 - OFF)",
                          RadioSettingValueInteger(0, 200, tmpch))
        scanl.append(rs)

        tmpch = _mem.scanlist1_priority_ch2 + 1
        if tmpch > 200:
            tmpch = 0
        rs = RadioSetting("scanlist1_priority_ch2",
                          "Scanlist 1 priority channel 2 (0 - OFF)",
                          RadioSettingValueInteger(0, 200, tmpch))
        scanl.append(rs)

        tmppr = bool((_mem.scanlist2_priority_scan & 1) > 0)
        rs = RadioSetting(
                "scanlist2_priority_scan",
                "Scanlist 2 priority channel scan",
                RadioSettingValueBoolean(tmppr))
        scanl.append(rs)

        tmpch = _mem.scanlist2_priority_ch1 + 1
        if tmpch > 200:
            tmpch = 0
        rs = RadioSetting("scanlist2_priority_ch1",
                          "Scanlist 2 priority channel 1 (0 - OFF)",
                          RadioSettingValueInteger(0, 200, tmpch))
        scanl.append(rs)

        tmpch = _mem.scanlist2_priority_ch2 + 1
        if tmpch > 200:
            tmpch = 0
        rs = RadioSetting("scanlist2_priority_ch2",
                          "Scanlist 2 priority channel 2 (0 - OFF)",
                          RadioSettingValueInteger(0, 200, tmpch))
        scanl.append(rs)

        # basic settings

        # call channel
        tmpc = _mem.call_channel+1
        if tmpc > 200:
            tmpc = 1
        rs = RadioSetting("call_channel", "One key call channel",
                          RadioSettingValueInteger(1, 200, tmpc))
        basic.append(rs)

        # Keypad locked
        rs = RadioSetting(
                "key_lock",
                "Keypad lock",
                RadioSettingValueBoolean(bool(_mem.key_lock > 0)))
        basic.append(rs)

        # Auto keypad lock
        rs = RadioSetting(
                "auto_keypad_lock",
                "Auto keypad lock (KeyLck)",
                RadioSettingValueBoolean(bool(_mem.auto_keypad_lock > 0)))
        basic.append(rs)

        # TOT
        tmptot = _mem.max_talk_time
        if tmptot > 10:
            tmptot = 10
        rs = RadioSetting(
                "tot",
                "Max talk time (TxTOut) [min]",
                RadioSettingValueInteger(0, 10, tmptot))
        basic.append(rs)

        # Battery save
        tmpbatsave = _mem.battery_save
        if tmpbatsave >= len(BATSAVE_LIST):
            tmpbatsave = BATSAVE_LIST.index("1:4")
        rs = RadioSetting(
                "battery_save",
                "Battery Save (BatSav)",
                RadioSettingValueList(
                    BATSAVE_LIST,
                    BATSAVE_LIST[tmpbatsave]))
        basic.append(rs)

        # NOAA autoscan
        rs = RadioSetting(
                "noaa_autoscan",
                "NOAA Autoscan (NOAA-S)", RadioSettingValueBoolean(
                    bool(_mem.noaa_autoscan > 0)))
        if _mem.BUILD_OPTIONS.ENABLE_NOAA:
            basic.append(rs)

        # Mic gain
        tmpmicgain = _mem.mic_gain
        if tmpmicgain > 4:
            tmpmicgain = 4
        rs = RadioSetting("mic_gain", "Mic Gain (Mic)",
                          RadioSettingValueInteger(0, 4, tmpmicgain))
        basic.append(rs)
                  
        # Mic_bar
        rs = RadioSetting(
                "Multi_option.Setting_mic_bar",
                "Microphone Bar display (MicBar)",
                RadioSettingValueBoolean(
                    bool(_mem.Multi_option.Setting_mic_bar > 0)))
        basic.append(rs)

        # Channel display mode
        tmpchdispmode = _mem.channel_display_mode
        if tmpchdispmode >= len(CHANNELDISP_LIST):
            tmpchdispmode = 0
        rs = RadioSetting(
                "channel_display_mode",
                "Channel display mode (ChDisp)",
                RadioSettingValueList(
                    CHANNELDISP_LIST,
                    CHANNELDISP_LIST[tmpchdispmode]))
        basic.append(rs)

        # Power on display mode
        tmpdispmode = _mem.power_on_dispmode
        if tmpdispmode >= len(WELCOME_LIST):
            tmpdispmode = 0
        rs = RadioSetting(
                "welcome_mode",
                "Power ON display message (POnMsg)",
                RadioSettingValueList(
                    WELCOME_LIST,
                    WELCOME_LIST[tmpdispmode]))
        basic.append(rs)
        
        # Logo string 1
        logo1 = str(_mem.logo_line1).strip("\x20\x00\xff") + "\x00"
        logo1 = _getstring(logo1.encode('ascii', errors='ignore'), 0, 12)
        rs = RadioSetting("logo1", "Message line 1 (MAX 12 characters)",
                          RadioSettingValueString(0, 12, logo1))
        basic.append(rs)

        # Logo string 2
        logo2 = str(_mem.logo_line2).strip("\x20\x00\xff") + "\x00"
        logo2 = _getstring(logo2.encode('ascii', errors='ignore'), 0, 12)
        rs = RadioSetting("logo2", "Message line 2 ( MAX 12 characters)",
                          RadioSettingValueString(0, 12, logo2))
        basic.append(rs)

       # Bat_txt
        tmpbattxt = _mem.Multi_option.Setting_battery_text
        if tmpbattxt >= len(BAT_TXT_LIST):
            tmpbattxt = 0

        rs = RadioSetting("Multi_option.Setting_battery_text",
                          "Battery Level Display (BatTXT)",
                          RadioSettingValueList(
                              BAT_TXT_LIST,
                              BAT_TXT_LIST[tmpbattxt]))
        basic.append(rs) 

        # Backlight auto mode
        tmpback = _mem.backlight_auto_mode
        if tmpback >= len(BACKLIGHT_LIST):
            tmpback = 0
        rs = RadioSetting("backlight_auto_mode",
                          "Backlight auto mode (BackLt)",
                          RadioSettingValueList(
                              BACKLIGHT_LIST,
                              BACKLIGHT_LIST[tmpback]))
        basic.append(rs)
        # Backlight min
        tmpback = _mem.backlight.backlight_min
        if tmpback >= len(BACKLIGHT_LVL_LIST):
            tmpback = 0
        rs = RadioSetting("backlight.backlight_min",
                          "Backlight level min (BLMin)",
                          RadioSettingValueList(
                              BACKLIGHT_LVL_LIST,
                              BACKLIGHT_LVL_LIST[tmpback]))
        basic.append(rs)
        
        # Backlight max
        tmpback = _mem.backlight.backlight_max
        if tmpback >= len(BACKLIGHT_LVL_LIST):
            tmpback = 0
        rs = RadioSetting("backlight.backlight_max",
                          "Backlight level max (BLMax)",
                          RadioSettingValueList(
                              BACKLIGHT_LVL_LIST,
                              BACKLIGHT_LVL_LIST[tmpback]))
        basic.append(rs)
        
        # Backlight TX_RX
        tmpback = _mem.Multi_option.Setting_backlight_on_TX_RX
        if tmpback >= len(BACKLIGHT_TX_RX_LIST):
            tmpback = 0
        rs = RadioSetting("Multi_option.Setting_backlight_on_TX_RX",
                          "Backlight on TX/RX (BltTRX)",
                          RadioSettingValueList(
                              BACKLIGHT_TX_RX_LIST,
                              BACKLIGHT_TX_RX_LIST[tmpback]))
        basic.append(rs)

        # Beep control
        rs = RadioSetting(
                "button_beep",
                "Key press beep sound (Beep)",
                RadioSettingValueBoolean(bool(_mem._0xe90.button_beep > 0)))
        basic.append(rs)

        # Reminding of end of talk
        tmpalarmmode = _mem.reminding_of_end_talk_ROGER
        if tmpalarmmode >= len(REMENDOFTALK_LIST):
            tmpalarmmode = 0
        rs = RadioSetting(
                "reminding_of_end_talk_ROGER",
                "Reminding of end of talk (Roger)",
                RadioSettingValueList(
                    REMENDOFTALK_LIST,
                    REMENDOFTALK_LIST[tmpalarmmode]))
        basic.append(rs)
       
        # Tail tone elimination
        rs = RadioSetting(
                "tail_note_elimination",
                "Tail tone elimination (STE)",
                RadioSettingValueBoolean(
                    bool(_mem.tail_note_elimination > 0)))
        basic.append(rs)
        
        # Repeater tail tone elimination
        tmprte = _mem.repeater_tail_elimination
        if tmprte >= len(RTE_LIST):
            tmprte = 0
        rs = RadioSetting(
                "repeater_tail_elimination",
                "Repeater tail tone elimination (RP STE)",
                RadioSettingValueList(RTE_LIST, RTE_LIST[tmprte]))
        basic.append(rs)

        # AM_fix
        rs = RadioSetting(
                "Multi_option.Setting_AM_fix",
                "AM reception fix (AM Fix)",
                RadioSettingValueBoolean(
                    bool(_mem.Multi_option.Setting_AM_fix > 0)))
        if _mem.BUILD_OPTIONS.ENABLE_AM_FIX:
            basic.append(rs)

        # VOX
        tmpvox = (_mem.vox_level + 1) * _mem.vox_switch
        if tmpvox > 10:
            tmpvox = 10
        rs = RadioSetting("vox", "Voice-operated switch (VOX)", RadioSettingValueList(
            VOX_LIST, VOX_LIST[tmpvox]))
        if _mem.BUILD_OPTIONS.ENABLE_VOX:
            basic.append(rs)

        # RX_MODE
        tmprxmode = (bool(_mem.crossband) << 1) + bool(_mem.dual_watch)
        if tmprxmode >= len(RXMODE_LIST):
            tmprxmode = 0
        rs = RadioSetting("rx_mode", "RX Mode (RxMode)", RadioSettingValueList(
            RXMODE_LIST, RXMODE_LIST[tmprxmode]))
        basic.append(rs)

        # VFO open
        rs = RadioSetting("vfo_open", "Enable frequency mode",
                          RadioSettingValueBoolean(bool(_mem.vfo_open > 0)))
        basic.append(rs)

        # Scan resume mode
        tmpscanres = _mem.scan_resume_mode
        if tmpscanres >= len(SCANRESUME_LIST):
            tmpscanres = 0
        rs = RadioSetting(
                "scan_resume_mode",
                "Scan resume mode (ScnRev)",
                RadioSettingValueList(
                    SCANRESUME_LIST,
                    SCANRESUME_LIST[tmpscanres]))
        basic.append(rs)

        # Voice
        tmpvoice = _mem.voice
        if tmpvoice >= len(VOICE_LIST):
            tmpvoice = 0
        rs = RadioSetting("voice", "Voice", RadioSettingValueList(
            VOICE_LIST, VOICE_LIST[tmpvoice]))
        if _mem.BUILD_OPTIONS.ENABLE_VOICE:
            basic.append(rs)

        # Alarm mode
        tmpalarmmode = _mem.alarm_mode
        if tmpalarmmode >= len(ALARMMODE_LIST):
            tmpalarmmode = 0
        rs = RadioSetting("alarm_mode", "Alarm mode", RadioSettingValueList(
            ALARMMODE_LIST, ALARMMODE_LIST[tmpalarmmode]))
        if _mem.BUILD_OPTIONS.ENABLE_ALARM:
            basic.append(rs)

        # squelch
        tmpsq = _mem.squelch
        if tmpsq > 9:
            tmpsq = 1
        rs = RadioSetting("squelch", "Squelch (Sql)",
                          RadioSettingValueInteger(0, 9, tmpsq))
        basic.append(rs)

        # S-meter
        tmpS0 = -int(_mem.S0_S_meter_level_dbm)
        tmpS9 = -int(_mem.S9_S_meter_level_dbm)
        if tmpS0 > -90 or tmpS0 < -200 or tmpS9 > -50 or tmpS9 < -160:
            tmpS0 = -200
            tmpS9 = -160
        rs = RadioSetting("S0_S_meter_level_dbm",
                          "S-meter S0 level [dBm]",
                          RadioSettingValueInteger(-200, -90, tmpS0))
        basic.append(rs)
        rs = RadioSetting("S9_S_meter_level_dbm",
                          "S-meter S9 level [dBm]",
                          RadioSettingValueInteger(-160, -50, tmpS9))
        basic.append(rs)

        # Battery Type
        tmpbtype = _mem.Battery_type
        if tmpbtype >= len(BATTYPE_LIST): 
            tmpbtype = 0
        rs = RadioSetting(
            "Battery_type", "Battery Type (BatTyp)",
            RadioSettingValueList(BATTYPE_LIST, BATTYPE_LIST[tmpbtype]))
        basic.append(rs)

        # FM radio
        for i in range(1, 21):
            freqname = "FM_"+str(i)
            fmfreq = _mem.fmfreq[i-1]/10.0
            if fmfreq < FMMIN or fmfreq > FMMAX:
                rs = RadioSetting(freqname, freqname,
                                  RadioSettingValueString(0, 5, ""))
            else:
                rs = RadioSetting(freqname, freqname,
                                  RadioSettingValueString(0, 5, str(fmfreq)))

            fmradio.append(rs)

        # unlock settings

        # F-LOCK     
        def validate_int_flock( value):
            memVal = self._memobj.int_flock
            if memVal!=7 and value==FLOCK_LIST[7]:
                msg = "\"" + value + "\" can only be enabled from radio menu"
                raise InvalidValueError(msg)
            return value
        
        tmpflock = _mem.int_flock
        if tmpflock >= len(FLOCK_LIST):
            tmpflock = 0
        val = RadioSettingValueList(FLOCK_LIST, FLOCK_LIST[tmpflock])
        rs = RadioSetting("int_flock", "TX Frequency Lock (F Lock)", val)
        val.set_validate_callback(validate_int_flock)
        unlock.append(rs)

        # 200TX
        rs = RadioSetting("int_200tx", "Unlock 174-350MHz TX (Tx 200)",
                          RadioSettingValueBoolean(
                              bool(_mem.int_200tx > 0)))
        unlock.append(rs)

        # 350TX
        rs = RadioSetting("int_350tx", "Unlock 350-400MHz TX (Tx 350)",
                          RadioSettingValueBoolean(
                              bool(_mem.int_350tx > 0)))
        unlock.append(rs)

        # 500TX
        rs = RadioSetting("int_500tx", "Unlock 500-600MHz TX (Tx 500)",
                          RadioSettingValueBoolean(
                              bool(_mem.int_500tx > 0)))
        unlock.append(rs)

        # 350EN
        rs = RadioSetting("int_350en", "Unlock 350-400MHz RX (350 En)",
                          RadioSettingValueBoolean(
                              bool(_mem.int_350en > 0)))
        unlock.append(rs)

        # Scrambler enable
        rs = RadioSetting("int_scren", "Scrambler enabled (ScraEn)",
                          RadioSettingValueBoolean(
                              bool(_mem.int_scren > 0)))
        unlock.append(rs)

        # readonly info
        # Firmware
        if self.FIRMWARE_VERSION == "":
            firmware = "To get the firmware version please download"
            "the image from the radio first"
        else:
            firmware = self.FIRMWARE_VERSION

        val = RadioSettingValueString(0, 128, firmware)
        val.set_mutable(False)
        rs = RadioSetting("fw_ver", "Firmware Version", val)
        roinfo.append(rs)

        # TODO: remove showing the driver version when it's in mainline chirp
        # Driver version

        val = RadioSettingValueString(0, 128, DRIVER_VERSION)
        val.set_mutable(False)
        rs = RadioSetting("driver_ver", "Driver version", val)
        roinfo.append(rs)
      
        return top

    # Store details about a high-level memory to the memory map
    # This is called when a user edits a memory in the UI
    def set_memory(self, mem):
        number = mem.number-1

        # Get a low-level memory object mapped to the image
        _mem = self._memobj.channel[number]
        _mem4 = self._memobj
        # empty memory
        if mem.empty:
            _mem.set_raw("\xFF" * 16)
            if number < 200:
                _mem2 = self._memobj.channelname[number]
                _mem2.set_raw("\xFF" * 16)
                _mem4.channel_attributes[number].is_scanlist1 = 0
                _mem4.channel_attributes[number].is_scanlist2 = 0
                _mem4.channel_attributes[number].compander = 0
                _mem4.channel_attributes[number].is_free = 1
                _mem4.channel_attributes[number].band = 0x7
            return mem

        # clean the channel memory, restore some bits if it was used before
        if _mem.get_raw()[0] == "\xff":
            # this was an empty memory
            _mem.set_raw("\x00" * 16)
        else:
            # this memory was't empty, save some bits that we don't know the
            # meaning of, or that we don't support yet
            prev_0a = _mem.get_raw(asbytes=True)[0x0a] & SAVE_MASK_0A
            prev_0b = _mem.get_raw(asbytes=True)[0x0b] & SAVE_MASK_0B
            prev_0c = _mem.get_raw(asbytes=True)[0x0c] & SAVE_MASK_0C
            prev_0d = _mem.get_raw(asbytes=True)[0x0d] & SAVE_MASK_0D
            raw = bytes([0]*10 + [prev_0a, prev_0b, prev_0c, prev_0d, 0, 0])
            _mem.set_raw(raw)

        if number < 200:
            _mem4.channel_attributes[number].is_scanlist1 = 0
            _mem4.channel_attributes[number].is_scanlist2 = 0
            _mem4.channel_attributes[number].compander = 0
            _mem4.channel_attributes[number].is_free = 1
            _mem4.channel_attributes[number].band = 0x7

        # find band
        band = _find_band(self, mem.freq)

        # mode
        tmpMode = self.get_features().valid_modes.index(mem.mode)
        _mem.modulation = tmpMode / 2
        _mem.bandwidth = tmpMode % 2
        if mem.mode == "USB":
            _mem.bandwidth = 1 # narrow

        # frequency/offset
        _mem.freq = mem.freq/10
        _mem.offset = mem.offset/10

        if mem.duplex == "OFF" or mem.duplex == "":
            _mem.offset = 0
            _mem.shift = 0
        elif mem.duplex == '-':
            _mem.shift = FLAGS1_OFFSET_MINUS
        elif mem.duplex == '+':
            _mem.shift = FLAGS1_OFFSET_PLUS

        # set band
        if number < 200:
            _mem4.channel_attributes[number].is_free = 0
            _mem4.channel_attributes[number].band = band

        # channels >200 are the 14 VFO chanells and don't have names
        if number < 200:
            _mem2 = self._memobj.channelname[number]
            tag = mem.name.ljust(10) + "\x00"*6
            _mem2.name = tag  # Store the alpha tag

        # tone data
        self._set_tone(mem, _mem)

        # step
        _mem.step = STEPS.index(mem.tuning_step)

        # tx power
        if str(mem.power) == str(UVK5_POWER_LEVELS[2]):
            _mem.txpower = POWER_HIGH
        elif str(mem.power) == str(UVK5_POWER_LEVELS[1]):
            _mem.txpower = POWER_MEDIUM
        else:
            _mem.txpower = POWER_LOW

        for setting in mem.extra:
            sname = setting.get_name()
            svalue = setting.value.get_value()

            if sname == "busyChLockout":
                _mem.busyChLockout = bool(svalue)

            if sname == "pttid":
                _mem.dtmf_pttid = PTTID_LIST.index(svalue)

            if sname == "frev":
                _mem.freq_reverse = bool(svalue)

            if sname == "dtmfdecode":
                _mem.dtmf_decode = bool(svalue)

            if sname == "scrambler":
                _mem.scrambler = SCRAMBLER_LIST.index(svalue)
                
            if sname == "compander":
                _mem4.channel_attributes[number].compander = \
                    COMPANDER_LIST.index(svalue)
                
            if number < 200 and sname == "scanlists":
                tmpVal = SCANLIST_LIST.index(svalue)
                _mem4.channel_attributes[number].is_scanlist1 = bool(tmpVal & 1)
                _mem4.channel_attributes[number].is_scanlist2 = bool(tmpVal & 2)

        return mem
