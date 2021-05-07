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

public class Hole extends Technical {

  /**
   * @param holeClosed  indicates whether the hole is closed (yes), open (no), or half-closed (half)
   */
  String holeClosed;

  public Hole(String holeClosed) throws IllegalArgumentException {
    super(holeClosed);
  }

  private String[] validTypes = new String[] { "yes", "no", "half" };

  public String toString() {
    return this.holeClosed;
  }
}
