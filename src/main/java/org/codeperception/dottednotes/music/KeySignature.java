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

public class KeySignature {

  int type;
  int[] modifiers;

  public KeySignature(int type) {
    this.type = type;
    this.modifiers = calculateModifiers(type);
  }

  public int getType() {
    return this.type;
  }

  private int[] calculateModifiers(int type) {
    int numModifiers = Math.abs(type);
    int[] modifiers = new int[numModifiers];
    if (type == 0) {
      return modifiers;
    } else if (type < 0) {
      for (int i = 0; i < numModifiers; i++) {
        modifiers[i] = FLATS[i];
      }
    } else if (type > 0) {
      for (int i = 0; i < numModifiers; i++) {
        modifiers[i] = SHARPS[i];
      }
    }
    return modifiers;
  }

  public int[] getModifiers() {
    return this.modifiers;
  }

  public int getModifier(Pitch pitch) {
    int[] modifiers = this.modifiers;
    if (modifiers.length <= 0) {
      return 0;
    }
    for (int i = 0; i < modifiers.length; i++) {
      int modifier = modifiers[i];
      if (modifier == pitch.getStep()) {
        if (this.type < 1) {
          return -1;
        } else if (this.type > 1) {
          return 1;
        }
      }
    }
    return 0;
  }

  private static final int[] SHARPS = { 3, 0, 4, 1, 5, 2, 6 };
  private static final int[] FLATS = { 6, 2, 5, 1, 4, 0, 3 };
}
