import pyb
import os

 
data = "X3";    # patte connectée à l'entrée série du MAX7219 (DIN)
load = "X2";    # patte de chargement des données (CS)
clk  = "X1";    # patte donnant l'horloge de la liaison série (CLK)
 
# Initialisation des pattes en sortie en mode push-pull
dataPin = pyb.Pin(data, pyb.Pin.OUT_PP)
loadPin = pyb.Pin(load, pyb.Pin.OUT_PP)
clkPin  = pyb.Pin(clk, pyb.Pin.OUT_PP)
 
# Mise à zéro des pattes
dataPin.low()
loadPin.low()
clkPin.low()
 
# Transmet un octet bit par bit vers le MAX7219, bit de poids fort en premier
def serialShiftByte(data):
    # Mise à zéro du signal d'horloge pour pouvoir faire un front montant plus tard
    clkPin.low()
    # Décalage des 8 bits de données
    for i in range(8):
        # on décale la donnée de i bits vers la gauche et on teste le bit de poids fort
        value = ((data << i) & 0B10000000) != 0
        dataPin.value(value)  # on met la patte DIN à cette valeur
        clkPin.high()         # puis on crée une impulsion sur CLK
        clkPin.low()          # pour transmettre ce bit
 
# Écriture d'une donnée dans un registre du MAX7219.
def serialWrite(address, data):
    # Mise à zéro du signal CS pour pouvoir créer un front montant plus tard
    loadPin.low()
    # On envoie l'adresse en premier
    serialShiftByte(address)
    # puis la donnée
    serialShiftByte(data)
    # et on crée une impulsion sur la ligne CS pour charger la donnée dans le registre
    loadPin.high()
    loadPin.low()

def matrixOn(on):
 if on:
  serialWrite(0x0c,1)
 else:
  serialWrite(0x0c,0)

def matrixTest(test):
 if test:
  serialWrite(0x0f,1)
 else:
  serialWrite(0x0f,0)

def matrixIntensity(percent):
 serialWrite(0x0a,int(15*percent/100))

def matrixDecode(decode):
 if decode:
  serialWrite(0x09, 0xff)
 else:
  serialWrite(0x09,0)

def matrixDigits(num):
 serialWrite(0x0b, num)

def matrixLine(num,value):
 serialWrite(num, value)

bitmap=bytearray(8)



def updateDisplay(bitmap):
 for k in range(8):
  serialWrite((k+1),bitmap[k])

def clearDisplay(bitmap):
 bitmap=bytearray(8)
 updateDisplay(bitmap)

def setPixel(x,y,on,bitmap):
 if on:
  bitmap[x]=bitmap[x] | (1 << y)
 else:
  bitmap[x]=bitmap[x] & ~(1 << y)
 

def getPixel(x,y,bitmap):
 return(bool(bitmap[x]>>y & 1))

def testPixels():
    bitmap = bytearray(8)
    matrixOn(1)
    matrixTest(0)
    matrixDecode(0)
    clearDisplay(bitmap)
    # Trace un O
    setPixel(1,2,1, bitmap); setPixel(2,2,1, bitmap); setPixel(3,2,1, bitmap)
    setPixel(1,3,1, bitmap);                          setPixel(3,3,1, bitmap)
    setPixel(1,4,1, bitmap);                          setPixel(3,4,1, bitmap)
    setPixel(1,5,1, bitmap); setPixel(2,5,1, bitmap); setPixel(3,5,1, bitmap)
    # Trace un K
    setPixel(5,2,1, bitmap);                          setPixel(7,2,1, bitmap)
    setPixel(5,3,1, bitmap); setPixel(6,3,1, bitmap)
    setPixel(5,4,1, bitmap); setPixel(6,4,1, bitmap)
    setPixel(5,5,1, bitmap);                          setPixel(7,5,1, bitmap)
    updateDisplay(bitmap)
 
def testPixels2():
    bitmap = bytearray(8)
    matrixOn(True)
    matrixTest(False)
    matrixDecode(False)
    matrixDigits(7)
    clearDisplay(bitmap)
    x = 0
    y = 0
    for k in range(65):
        setPixel(x, y, True, bitmap)
        updateDisplay(bitmap)
        setPixel(x, y, False, bitmap)
        x = (x + 1) % 8
        if x == 0:
            y = (y + 1) % 8
        pyb.delay(100)
    clearDisplay(bitmap)

smiley = (
    "  ****  ",
    " *    * ",
    "* *  * *",
    "*      *",
    "* *  * *",
    "*  **  *",
    " *    * ",
    "  ****  "
)
frowney = (
    "  ****  ",
    " *    * ",
    "* *  * *",
    "*      *",
    "*  **  *",
    "* *  * *",
    " *    * ",
    "  ****  "
)

def displayPict(pict):
 bitmap=bytearray(8)
 for k in range(len(pict)):
  for i in range(len(list(pict[k]))):
   if list(pict[k])[i]==" ":
    setPixel(k,i,0,bitmap)
   else:
    setPixel(k,i,1,bitmap)
 updateDisplay(bitmap)
 return bitmap

def randomBitmap():
 bitmap=bytearray(8)
 for i in range(8):
  for j in range(8):
   if os.urandom(1)[0] < 128 :
    setPixel(i,j,1,bitmap)
 return bitmap

def countNeighbours(x,y,bitmap):
 counter=0
 for i in range(-1,2):
  for j in range(-1,2):
   if (i,j)!=(0,0):
    counter+=int(getPixel((x+i)%8,(y+j)%8,bitmap))
 return counter

def lifeStep(bitmap):
 bitmap1=bytearray(8)
 for k in range(8):
  bitmap1[k]=bitmap[k]
 for i in range(8):
  for j in range(8):
   if countNeighbours(i,j,bitmap1)==3:
    setPixel(i,j,1,bitmap)
   elif countNeighbours(i,j,bitmap1)!=2:
    setPixel(i,j,0,bitmap)
 updateDisplay(bitmap)

def gameOfLife(N):
 bitmap=randomBitmap()
 for k in range(N):
  lifeStep(bitmap)
  pyb.delay(200)

# Figures stables
stableBlock = (
  "        ",
  "        ",
  "        ",
  "   **   ",
  "   **   ",
  "        ",
  "        ",
  "        "
)
def testBlock():
    bitmap = displayPict(stableBlock)
    pyb.delay(500)
    lifeStep(bitmap)
 
stableTube = (
  "        ",
  "        ",
  "   *    ",
  "  * *   ",
  "   *    ",
  "        ",
  "        ",
  "        "
)
def testTube():
    bitmap = displayPict(stableTube)
    pyb.delay(500)
    lifeStep(bitmap)
 
# Figures oscillantes
oscBlinker = (
  "        ",
  "        ",
  "        ",
  "  ***   ",
  "        ",
  "        ",
  "        ",
  "        "
)
def testBlinker():
    bitmap = displayPict(oscBlinker)
    for i in range(10):
        pyb.delay(500)
        lifeStep(bitmap)
 
# Vaisseaux
shipGlider = (
  "        ",
  "        ",
  "        ",
  "        ",
  "        ",
  "***     ",
  "  *     ",
  " *      "
)
def testGlider():
    bitmap = displayPict(shipGlider)
    for i in range(32):
        pyb.delay(500)
        lifeStep(bitmap)
 
shipLWSS = (
  "        ",
  "        ",
  "*  *    ",
  "    *   ",
  "*   *   ",
  " ****   ",
  "        ",
  "        "
)
def testLWSS():
    bitmap = displayPict(shipLWSS)
    for i in range(64):
        pyb.delay(50)
        lifeStep(bitmap) 


