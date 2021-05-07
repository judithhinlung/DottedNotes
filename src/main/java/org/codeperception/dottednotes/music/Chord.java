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

import java.util.ArrayList;
import org.codeperception.dottednotes.math.Fraction;

public class Chord extends MeasureElement {

  ArrayList<Note> notes;

  public Chord(Measure measure) {
    super(measure);
    notes = new ArrayList<Note>();
  }

  public ArrayList<Note> getNotes() {
    return this.notes;
  }

  public void addNote(Note note) {
    this.notes.add(note);
  }

  public void setDuration(Fraction duration) {
    this.duration = duration;
  }

  public int getStaffNumber() {
    return this.notes.get(0).getStaffNumber();
  }

  public void setStaffNumber(int staffNumber) {
    for (int i = 0; i < this.notes.size(); i++) {
      Note note = notes.get(i);
      note.setStaffNumber(staffNumber);
    }
  }

  public int getVoiceNumber() {
    return this.notes.get(0).getVoiceNumber();
  }

  public void setVoiceNumber(int voiceNumber) {
    for (int i = 0; i < this.notes.size(); i++) {
      Note note = notes.get(i);
      note.setVoiceNumber(voiceNumber);
    }
  }
}
