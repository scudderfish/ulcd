from time import *
from machine import I2C

# from i2c-dev.h
I2C_SLAVE = 0x0703

LCD_CLEARDISPLAY    =    0x01
LCD_RETURNHOME      =    0x02
LCD_ENTRYMODESET    =    0x04
LCD_DISPLAYCONTROL  =    0x08
LCD_CURSORSHIFT     =    0x10
LCD_FUNCTIONSET     =    0x20
LCD_SETCGRAMADDR    =    0x40
LCD_SETDDRAMADDR    =    0x80

# flags for display entry mode
# ---------------------------------------------------------------------------
LCD_ENTRYRIGHT          = 0x00
LCD_ENTRYLEFT           = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off and cursor control
# ---------------------------------------------------------------------------
LCD_DISPLAYON      =     0x04
LCD_DISPLAYOFF     =     0x00
LCD_CURSORON       =     0x02
LCD_CURSOROFF      =     0x00
LCD_BLINKON        =     0x01
LCD_BLINKOFF       =     0x00

# flags for display/cursor shift
# ---------------------------------------------------------------------------
LCD_DISPLAYMOVE   =      0x08
LCD_CURSORMOVE    =      0x00
LCD_MOVERIGHT     =      0x04
LCD_MOVELEFT      =      0x00

# flags for function set
# ---------------------------------------------------------------------------
LCD_8BITMODE     =       0x10
LCD_4BITMODE     =       0x00
LCD_2LINE        =       0x08
LCD_1LINE        =       0x00
LCD_5x10DOTS     =       0x04
LCD_5x8DOTS      =       0x00


COMMAND          = 0
DATA             = 1
FOUR_BITS        = 2
LCD_NOBACKLIGHT  = 0x00
LCD_BACKLIGHT    = 0xFF
POSITIVE         = 0
NEGATIVE         = 1

row_offsetsDef   = [0x00, 0x40, 0x14, 0x54]
row_offsetsLarge = [0x00, 0x40, 0x10, 0x50]

# General i2c device class so that other devices can be added easily
class i2c_lcd:
            
    def __init__(self, addr, port,En_pin,Rw_pin,Rs_pin,D4_pin,D5_pin,D6_pin,D7_pin):
        self.i2c                       = I2C(0, I2C.MASTER, baudrate=100000, pins=('GP15', 'GP10'))
        self.addr                      = addr
        self._data_pins                = [0]*4;
        self._En                       = (1 << En_pin);
        self._Rw                       = (1 << Rw_pin);
        self._Rs                       = (1 << Rs_pin);
        self._data_pins[0]             = (1 << D4_pin);
        self._data_pins[1]             = (1 << D5_pin);
        self._data_pins[2]             = (1 << D6_pin);
        self._data_pins[3]             = (1 << D7_pin);
        self._backlightPinMask         = 0;
        self._backlightStsMask         = LCD_NOBACKLIGHT;
        self._polarity                 = POSITIVE;
        self.debugFlag                 = False
        
    def writeByte(self, byte):
        self.debug("WRITE %x" % byte) 
        self.dev[self.addr]= byte

    def write(self, byte,mode):
        self.debug( "WRITEMODE %x %x" % (byte,mode))

        if (mode == FOUR_BITS):
            self.write4bits((byte & 0x0F),COMMAND)
        else:
            self.write4bits((byte >> 4),mode);
            self.write4bits((byte & 0x0F),mode);

    def write4bits(self,value,mode):
        pinMapValue = 0;
        for i in range(0,4):
            if ((value & 0x1) == 1):
                pinMapValue |= self._data_pins[i];
            value = (value >> 1 );
        
        if ( mode == DATA):
            mode=self._Rs
        
        self.debug( "WRITE4(%x,%x,backlight=%x)" % (pinMapValue,mode,self._backlightStsMask))   
        pinMapValue |= mode | self._backlightStsMask;
        
        #print "WRITE4 %x" % pinMapValue 
        
        self.pulseEnable(pinMapValue);
        
    def pulseEnable(self,data):
        #print "pulseEnable %x" % (data | self._En)
        self.dev[-1]= (data | self._En);
        #print "pulseEnable %x" % (data & ~self._En)
        self.dev[-1] = (data & ~self._En);

    def read_nbytes_data(self, data, n): # For sequential reads > 1 byte
        return self.i2c.read_i2c_block_data(self.addr, data, n)

    def setBacklightPin(self,pin,pol):
        self.debug( "setBacklightPin(%x,%x)" % (pin,pol))
        self._backlightPinMask = ( 1 << pin );
        self._polarity = pol;
        self.setBacklight(LCD_NOBACKLIGHT);

    def setBacklight(self,value):
        self.debug("setBacklight (%x) Current state=%x" % (value,self._backlightStsMask))
        if ( self._backlightPinMask != 0x0 ):
            if  (((self._polarity == POSITIVE) and (value > 0)) or ((self._polarity == NEGATIVE ) and ( value == 0 ))):
                self._backlightStsMask = self._backlightPinMask & LCD_BACKLIGHT;
            else:
                self._backlightStsMask = self._backlightPinMask & LCD_NOBACKLIGHT;
            self.writeByte(self._backlightStsMask );
        self.debug("setBacklight new state = %x" % (self._backlightStsMask))
                
    def debug(self,msg):
        if (self.debugFlag):
            print (msg)
class lcd:
    #initialises objects and lcd
    def __init__(self, addr=0x27,En_pin=2,Rw_pin=1,Rs_pin=0,D4_pin=4,D5_pin=5,D6_pin=6,D7_pin=7):
        
        self.addr              = addr;
        self.port              = port;
        self.En_pin            = En_pin;
        self.Rw_pin            = Rw_pin;
        self.Rs_pin            = Rs_pin;
        self.D4_pin            = D4_pin;
        self.D5_pin            = D5_pin;
        self.D6_pin            = D6_pin;
        self.D7_pin            = D7_pin;
        
        self._displayfunction  = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS;
        self._numlines         = 2;
        self._cols             = 20;
        
    def init(self,cols,lines,dotsize):
        self.lcd_device = i2c_lcd(self.addr, self.port,self.En_pin,self.Rw_pin,
            self.Rs_pin,self.D4_pin,self.D5_pin,self.D6_pin,self.D7_pin)
        if (lines > 1): 
            self._displayfunction |= LCD_2LINE;

        self._numlines = lines;
        self._cols = cols;
        
        if ((dotsize != LCD_5x8DOTS) and (lines == 1)):
            _displayfunction |= LCD_5x10DOTS;

        sleep_ms(100);
        self.lcd_device.write(0x03,FOUR_BITS)
        sleep_ms(5)
        self.lcd_device.write(0x03,FOUR_BITS)
        sleep_ms(5)
        self.lcd_device.write(0x03,FOUR_BITS)
        sleep_ms(5)
        self.lcd_device.write(0x02,FOUR_BITS)
        sleep_ms(5)
            
        # finally, set # lines, font size, etc.
        self.command(LCD_FUNCTIONSET | self._displayfunction);  

        #turn the display on with no cursor or blinking default
        self._displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF;  
        self.display();

        #clear the LCD
        self.clear();

        #Initialise to default text direction (for romance languages)
        self._displaymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT;
        #set the entry mode
        self.command(LCD_ENTRYMODESET | self._displaymode);
        self.backlight();
        
    def command(self,value):
        self.lcd_device.write(value,COMMAND);
        
    def display(self):
        self._displaycontrol |= LCD_DISPLAYON;
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol);

    def home(self):
        self.command(LCD_RETURNHOME);
        sleep_ms(2)
        
    def clear(self):
        self.command(LCD_CLEARDISPLAY); 
        sleep_ms(2) 

    def backlight(self):
        self.setBacklight(LCD_BACKLIGHT)
        
    def setBacklightPin(self,pin,pol):
        self.lcd_device.setBacklightPin(pin,pol)
        
    def setBacklight(self,value):
        self.lcd_device.setBacklight(value);

    def begin(self,cols,rows):
        self.init(cols,rows,LCD_5x8DOTS);
        
    def write(self,value):
        for c in value:
            self.lcd_device.write(ord(c),DATA)
            
    def noDisplay(self):
        self._displaycontrol &= ~LCD_DISPLAYON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol);
        
        
    def display(self):
        self._displaycontrol |= LCD_DISPLAYON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol);
        
                    
    def setCursor(self,col,row):
        if(row >= self._numlines):
            row = self._numlines - 1;
            
        if (self._cols == 16 and self._numlines == 4):
            commandValue = LCD_SETDDRAMADDR | (col + row_offsetsLarge[row]);
        else:
            print ("offset value=%x"%row_offsetsDef[row])
            commandValue = LCD_SETDDRAMADDR | (col + row_offsetsDef[row]);

        self.command(commandValue)

    def test(self):
        self.begin(16,2)
        self.setbacklightPin(3)
        self.setBacklight(1)
        self.home()
        self.write("Hello World!\n")