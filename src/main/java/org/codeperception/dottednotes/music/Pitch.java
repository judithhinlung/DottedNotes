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

import org.codeperception.dottednotes.music.*;

/** Class for the note properties of pitch, unpitched, and rest
 */
public class Pitch {

  /**
   * The Pitch class represents the note properties of pitch, rest, and unpitched.
   */
  String type;
  int octave = -1;
  int step = -1;
  int alter = 0;

  public Pitch(String type, final int octave, final int step, final int alter) {
    String[] availableTypes = new String[] { "p", "u", "r" };
    if (!Utils.contains(type, availableTypes)) {
      throw new IllegalArgumentException("Invalid pitch type: " + type);
    }
    this.type = type;
    this.octave = octave;
    this.step = step;
    this.alter = alter;
  }

  public Pitch(String type, final int octave, final int step) {
    String[] availableTypes = new String[] { "p", "u", "r" };
    if (!Utils.contains(type, availableTypes)) {
      throw new IllegalArgumentException("Invalid pitch type: " + type);
    }
    this.type = type;
    this.octave = octave;
    this.step = step;
  }

  public Pitch(String type) throws IllegalArgumentException {
    String[] availableTypes = new String[] { "p", "u", "r" };
    if (!Utils.contains(type, availableTypes)) {
      throw new IllegalArgumentException("Invalid pitch type: " + type);
    }
  }

  public String getType() {
    return this.type;
  }

  public int getStep() {
    return this.step;
  }

  public int getAlter() {
    return this.alter;
  }

  public int getOctave() {
    return this.octave;
  }

  boolean isMeasureRest = false;

  public boolean getIsMeasureRest() {
    return this.isMeasureRest;
  }

  public void setIsMeasureRest(boolean rest) {
    this.isMeasureRest = rest;
  }

  private final int STEPS = 7;

  public Pitch getNextStep(int accidental) {
    int step = this.step;
    int alter = this.alter;
    int octave = this.octave;
    if (step < STEPS - 1) {
      step += 1;
    } else {
      step = 0;
      octave += 1;
    }
    return new Pitch("p", octave, step, alter);
  }

  public Pitch getNextStep(KeySignature key) {
    int step = this.step;
    int alter = this.alter;
    int octave = this.octave;
    if (step < STEPS - 1) {
      step += 1;
    } else {
      step = 0;
      octave += 1;
    }
    Pitch tmp = new Pitch("p", octave, step);
    alter = key.getModifier(tmp);
    return new Pitch("p", octave, step, alter);
  }

  public Pitch getPreviousStep(int accidental) {
    int step = this.step;
    int alter = this.alter;
    int octave = this.octave;
    if (step > 0) {
      step -= 1;
    } else {
      step = STEPS - 1;
      octave -= 1;
    }
    alter = accidental;
    return new Pitch("p", octave, step, alter);
  }

  public Pitch getPreviousStep(KeySignature key) {
    int step = this.step;
    int alter = this.alter;
    int octave = this.octave;
    if (step > 0) {
      step -= 1;
    } else {
      step = STEPS - 1;
      octave -= 1;
    }
    Pitch tmp = new Pitch("p", octave, step);
    alter = key.getModifier(tmp);
    return new Pitch("p", octave, step, alter);
  }

  public int getMidiPitch() {
    int midiPitch = 0;
    midiPitch = ((this.octave + 1) * 12) + this.getChromaticStep() + this.alter;
    return midiPitch;
  }

  int getChromaticStep() {
    int[] chromaticSteps = new int[] { 0, 2, 4, 5, 7, 9, 11 };
    return chromaticSteps[this.step];
  }
}
