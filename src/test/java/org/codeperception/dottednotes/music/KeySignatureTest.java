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

public class KeySignatureTest extends TestCase {

  //-----------------//
  // testKeySignatureInstantiation
  //-----------------//
  @Test
  public void testKeySignatureInstantiation() {
    KeySignature key = new KeySignature(0);
    assertEquals(key.getModifiers().length, 0);
    key = new KeySignature(1);
    assertEquals(key.getModifiers().length, 1);
    assertEquals(key.getModifiers()[0], 3);
    key = new KeySignature(-1);
    assertEquals(key.getModifiers().length, 1);
    assertEquals(key.getModifiers()[0], 6);
    key = new KeySignature(4);
    assertEquals(key.getModifiers().length, 4);
    assertEquals(key.getModifiers()[1], 0);
    assertEquals(key.getModifiers()[3], 1);
  }

  /**
   * Tests that a given pitch returns the correct modifier,
   * +1 for sharp, 0 for natural, -1 for flat,
   * based on a given key signature.
   * Used in conversions from file formats that
   * do not support the alter element.
   */

  public void testGetModifierForGivenPitch() {
    KeySignature key = new KeySignature(2);
    Pitch pitch = new Pitch("p", 4, 3, 0);
    assertEquals(key.getModifier(pitch), 1);
    pitch = new Pitch("p", 3, 1, 0);
    assertEquals(key.getModifier(pitch), 0);
    key = new KeySignature(-2);
    pitch = new Pitch("p", 4, 6, 0);
    assertEquals(key.getModifier(pitch), -1);
    pitch = new Pitch("p", 4, 3, 0);
    assertEquals(key.getModifier(pitch), 0);
  }
}
