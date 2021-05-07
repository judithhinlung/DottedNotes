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

public class Accidental {

  String type;

  public Accidental(String type) throws IllegalArgumentException {
    if (!Utils.contains(type, validTypes)) {
      throw new IllegalArgumentException("Unsupported type: " + type);
    }
    this.type = type;
  }

  public String getType() {
    return this.type;
  }

  private String[] validTypes = new String[] {
    "sharp",
    "natural",
    "flat",
    "double-sharp",
    "sharp-sharp",
    "flat-flat",
    "natural-sharp",
    "natural-flat",
    "quarter-flat",
    "quarter-sharp",
    "three-quarters-flat",
    "three-quarters-sharp",
    "sharp-down",
    "sharp-up",
    "natural-down",
    "natural-up",
    "flat-down",
    "flat-up",
    "double-sharp-down",
    "double-sharp-up",
    "flat-flat-down",
    "flat-flat-up",
    "arrow-down",
    "arrow-up",
    "triple-sharp",
    "triple-flat",
    "slash-quarter-sharp",
    "slash-sharp",
    "slash-flat",
    "double-slash-flat",
    "sharp-1",
    "sharp-2",
    "sharp-3",
    "sharp-5",
    "flat-1",
    "flat-2",
    "flat-3",
    "flat-4",
    "sori",
    "koron",
  };

  /**
   * Returns the number of semitones that should be added
   * to a note based on
   * the accidental type,
   * e.g. -1 for flat, 1 for shar.
   *
   * @return  An integer representing the chromatic steps to be added to a note
   */
  public int getModifier() {
    if (this.type.equals("sharp-sharp") || this.type.equals("double-sharp")) {
      return 2;
    } else if (this.type.equals("sharp")) {
      return 1;
    } else if (this.type.equals("natural")) {
      return 0;
    } else if (this.type.equals("flat")) {
      return -1;
    } else if (this.type.equals("flat-flat")) {
      return -2;
    }
    return 0;
  }
}
