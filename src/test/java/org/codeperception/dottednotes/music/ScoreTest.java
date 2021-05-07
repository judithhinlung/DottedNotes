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
import junit.framework.TestCase;
import org.codeperception.dottednotes.math.Fraction;
import org.junit.Test;

public class ScoreTest extends TestCase {

  //-----------------//
  // testGetDivisions
  //-----------------//
  @Test
  public void testGetDivisions() {
    Score score = new Score();
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    m1.setDivisions(24);
    p1.addMeasure(m1);
    score.addPart(p1);
    assertEquals(p1.getCurrentDivisions(1), 24);
    assertEquals(score.getDivisions(), 24);
  }
}
