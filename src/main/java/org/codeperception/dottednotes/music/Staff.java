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
import java.util.HashMap;

public class Staff {

  int number;
  HashMap<Integer, Voice> voices;

  public Staff(int number) {
    this.number = number;
    this.voices = new HashMap<Integer, Voice>();
  }

  public int getNumber() {
    return this.number;
  }

  public boolean hasVoice(int voice) {
    return this.voices.containsKey(voice);
  }

  public void addVoice(Voice voice) {
    this.voices.put(voice.getNumber(), voice);
  }

  public Voice getVoice(int number) {
    if (this.voices.containsKey(number)) {
      return this.voices.get(number);
    }
    return null;
  }

  public HashMap<Integer, Voice> getVoices() {
    return this.voices;
  }
}
