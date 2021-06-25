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

package org.codeperception.dottednotes.converters.braille;

import junit.framework.TestCase;
import org.codeperception.dottednotes.math.Fraction;
import org.codeperception.dottednotes.music.*;
import org.junit.Test;

public class SignTest extends TestCase {

  //-----------------//
  // testToUnicodeBraille
  //-----------------//
  @Test
  public void testToUnicodeBraille() {
    Sign sign = new Sign(1);
    assertEquals("⠁", sign.toUnicode());
    sign = new Sign(125);
    assertEquals("⠓", sign.toUnicode());
    sign = new Sign(123456);
    assertEquals("⠿", sign.toUnicode());
  }

  //-----------------//
  // testToUnicodeBraille
  //-----------------//

  public void testToAsciiBraille() {
    Sign sign = new Sign(1);
    assertEquals("a", sign.toAscii());
    sign = new Sign(3);
    assertEquals("\'", sign.toAscii());
    sign = new Sign(1256);
    assertEquals("\\", sign.toAscii());
    sign = new Sign(12356);
    assertEquals("(", sign.toAscii());
  }
}
