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

/** Indicates that a note is part of an arpeggiated chord */
public class Arpeggiate {

  /**
   * @param number  Used to distinguish between two simultaneous arpeggiated chords
   * @param direction  up/down, indicates the direction of the arpeggio
   */
  int number;
  String direction;

  public Arpeggiate() {
    this.direction = "up";
    this.number = 0;
  }

  public Arpeggiate(int number, String direction) throws IllegalArgumentException {
    if (!(direction.equals("up")) || (direction.equals("down"))) {
      throw new IllegalArgumentException("Invalid arpeggiate direction: " + direction);
    }
    this.number = number;
    this.direction = direction;
  }

  public int getNumber() {
    return this.number;
  }

  public String getDirection() {
    return this.direction;
  }
}
