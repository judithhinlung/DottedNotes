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

import org.codeperception.dottednotes.math.AbstractFraction;
import org.codeperception.dottednotes.math.Fraction;

public class MeasureElement {

  Measure measure;

  public MeasureElement(Measure measure) {
    this.measure = measure;
  }

  public Measure getMeasure() {
    return this.measure;
  }

  Fraction moment = Fraction.ZERO;

  public Fraction getMoment() {
    return this.moment;
  }

  public void setMoment(Fraction moment) {
    this.moment = moment;
  }

  int staffNumber = 1;

  public int getStaffNumber() {
    return this.staffNumber;
  }

  public void setStaffNumber(int staffNumber) {
    this.staffNumber = staffNumber;
  }

  int voiceNumber = 1;

  public int getVoiceNumber() {
    return this.voiceNumber;
  }

  public void setVoiceNumber(int voiceNumber) {
    this.voiceNumber = voiceNumber;
  }

  Fraction duration = Fraction.ZERO;

  public Fraction getDuration() {
    return this.duration;
  }
}
