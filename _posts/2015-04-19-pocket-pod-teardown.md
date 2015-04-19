---
layout: default
title: Line 6 Pocket POD Teardown
---

# Line 6 Pocket POD Teardown

Just a quick post showing the insides of a [Line 6 Pocket
POD](http://uk.line6.com/pocketpod/):

![PCB Front](/assets/pocket-pod/pcb_front.jpg)
![PCB Back](/assets/pocket-pod/pcb_back.jpg)

The chip at the top is a [AKM
AK4556](http://pdf1.alldatasheet.net/datasheet-pdf/view/206731/AKM/AK4556VT/+Q05JW_VYpLawLNvzwcb+/datasheet.pdf)
ADC/DAC.

The other chips are, from left to right:

* [ISSI IS62WV5128BLL](http://www.issi.com/WW/pdf/62WV5128ALL.pdf) 512K x 8 low
  voltage, ultra low power CMOS static RAM.
* [Freescale DSP56364](http://www.freescale.com/webapp/sps/site/prod_summary.jsp?code=DSP56364) 24-Bit Audio Digital Signal
  Processor.
* [LVC74A?](http://www.ti.com/lit/ds/symlink/sn74lvc74a.pdf) dual positive-edge-triggered D-type flip-flops with clear and preset.
* [NXP LPC2148](http://www.nxp.com/documents/data_sheet/LPC2141_42_44_46_48.pdf) single-chip
  ARM microcontroller with 512kB Flash memory.

