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

import org.codeperception.dottednotes.math.Fraction;

public class Forward extends MeasureElement {

  /**
   * The Forward object is used to coordinate multiple voices in one part.
   *
   * @param measure  Measure the Forward object belongs to
   */

  Measure measure;

  public Forward(Measure measure, Fraction duration) {
    super(measure);
    this.duration = duration;
  }
}
