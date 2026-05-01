# Space-Clock
**Program code and build guide for the space clock.**

**The space clock is a matrix clock in which the time is determined by counting the number of illuminated light squares.**


---

## Materials

- IKEA Rödalm picture frame (15×13 cm)  
- WS2812B NeoPixel LED strip (60 LEDs/m)  
  - 3 to 5 strips with 9 LEDs each  
- ESP32 (recommended: ESP32-S2 Mini)  
- 3D-printed front panel  
- USB cable compatible with your ESP  

---

## Assembly Instructions

### 1. Prepare the Back Panel

Mark the layout on the back panel of the frame:

- Draw a cross to find the center (vertical and horizontal middle lines)  
- Add additional horizontal lines for each LED row  
- Keep equal spacing between rows (matching the LED spacing)  
- Minimum: **3 rows**  
- Recommended: **5 rows** (for more visual effects)

---

### 2. Attach LED Strips

⚠️ Pay attention to the **data direction** of the LED strips!

- With 5 rows:
  - Start at the bottom row  
  - Attach the strip **from right to left**  
  - Continue each row above in the same direction  

- Solder 3 wires (VCC, GND, DATA) to the **input side** of the bottom strip (left side)

- Connect each strip to the one above it at the ends (daisy chain)

---

### 3. Mount the ESP32

- Attach the ESP32 to the back of the frame  
- Connect:
  - **VCC**
  - **GND**
  - **DATA** (to a suitable GPIO pin)

---

## Programming

*(coming soon)*
