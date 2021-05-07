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

public class Transpose {

  int step = 0;
  int diatonicPitch = 0;
  int octaveChange = 0;
  int staffNumber = 0;

  public Transpose(int step) {
    this.step = step;
  }

  public int getStep() {
    return this.step;
  }

  public int getDiatonicPitch() {
    return this.diatonicPitch;
  }

  public void setDiatonicPitch(int diatonicPitch) {
    this.diatonicPitch = diatonicPitch;
  }

  public int getOctaveChange() {
    return this.octaveChange;
  }

  public void setOctaveChange(int octaveChange) {
    this.octaveChange = octaveChange;
  }

  public int getStaffNumber() {
    return this.staffNumber;
  }

  public void setStaffNumber(int number) {
    this.staffNumber = number;
  }

  boolean doubling = false;

  public boolean getDoubling() {
    return this.doubling;
  }

  public void setDoubling(boolean doubling) {
    this.doubling = doubling;
  }
}
