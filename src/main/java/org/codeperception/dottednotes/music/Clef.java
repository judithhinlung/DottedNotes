/**
 * DottedNotes: -- Braille Music Conversion Utility
 *
 * Copyright 2021 Judith Lung  All Rights Reserved.
 *
 * This code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 3, as
 * published by the Free Software Foundation.
 *
 * This code is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this work; if not, see <http://www.gnu.org/licenses/>.
 */

package org.codeperception.dottednotes.music;

public class Clef {

  String sign;
  int line = 0;
  int clefOctaveChange = 0;
  int staffNumber = 0;

  public Clef(String sign) {
    this.sign = sign;
  }

  public Clef(String sign, int line) {
    this.sign = sign;
    this.line = line;
  }

  public String getSign() {
    return this.sign;
  }

  public int getLine() {
    return this.line;
  }

  public int getStaffNumber() {
    return this.staffNumber;
  }

  public void setStaffNumber(int number) {
    this.staffNumber = number;
  }

  int octaveChange = 0;

  public int getOctaveChange() {
    return this.octaveChange;
  }

  public void setOctaveChange(int octaveChange) {
    this.octaveChange = octaveChange;
  }

  public boolean isTrebleCleff() {
    return (this.sign == "G" && this.line == 2);
  }

  public boolean isBassCleff() {
    return (this.sign == "F" && this.line == 4);
  }

  public boolean isAltoCleff() {
    return (this.sign == "C" && this.line == 3);
  }

  public boolean isTab() {
    return this.line == 5;
  }
}
