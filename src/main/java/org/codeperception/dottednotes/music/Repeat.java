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

public class Repeat {

  String direction;
  int times = 1;

  public Repeat(String direction) throws IllegalArgumentException {
    if (!Utils.contains(direction, validDirections)) {
      throw new IllegalArgumentException("Unknown repeat direction: " + direction);
    }
    this.direction = direction;
  }

  private String[] validDirections = new String[] { "forward", "backward" };

  public String getDirection() {
    return this.direction;
  }

  public int getTimes() {
    return this.times;
  }

  public void setTimes(int times) {
    this.times = times;
  }
}
