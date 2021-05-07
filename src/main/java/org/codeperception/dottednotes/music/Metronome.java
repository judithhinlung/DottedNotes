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

public class Metronome extends MeasureElement {

  /** Specifies metronome direction.
   *
   * @param measure  The measure this element belongs to
   * @param beatUnit   note type per beat
   * @param perMinute  Number of beats per minute
   */
  Measure measure;
  String beatUnit;
  int perMinute;

  public Metronome(Measure measure, String beatUnit, int perMinute)
    throws IllegalArgumentException {
    super(measure);
    String[] availableUnits = new String[] {
      "1024th",
      "512th",
      "256th",
      "128th",
      "64th",
      "32nd",
      "16th",
      "eighth",
      "quarter",
      "half",
      "whole",
      "breve",
      "long",
      "maxima",
    };
    if (!Utils.contains(beatUnit, availableUnits)) {
      throw new IllegalArgumentException("Invalid beat unit: " + beatUnit);
    }
    this.beatUnit = beatUnit;
    this.perMinute = perMinute;
  }

  public String getBeatUnit() {
    return this.beatUnit;
  }

  public int getPerMinute() {
    return this.perMinute;
  }

  /**
   * The metronomeNote and metronomeRelation fields are
   * used in MusicXML to specify metric modulations
   * and other metric relations,
   * e.g. swing tempo marks.
   */
  Note metronomeNote;

  public Note getMetronomeNote() {
    return this.metronomeNote;
  }

  public void setMetronomeNote(Note note) {
    this.metronomeNote = note;
  }

  String metronomeRelation;

  public String getMetronomeRelation() {
    return this.metronomeRelation;
  }

  public void setMetronomeRelation(String relation) {
    this.metronomeRelation = relation;
  }
}
