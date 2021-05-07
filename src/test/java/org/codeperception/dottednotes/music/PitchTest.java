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
import org.junit.Test;

public class PitchTest extends TestCase {

  //-----------------//
  // testConvertToMidiPitch
  //-----------------//
  @Test
  public void testConvertToMidiPitch() {
    Pitch pitch = new Pitch("r", 4, 0);
    assertEquals(pitch.getMidiPitch(), 60);
    pitch = new Pitch("r", 4, 4);
    assertEquals(pitch.getMidiPitch(), 67);
  }

  /**
   * Checks that the correct neighboring pitch step is returned,
   * based on a specified accidental value or key signature.
   */
  //---------------//
  // testGetPreviousStep
  //---------------//
  public void testGetPreviousStepWithAccidental() {
    Pitch pitch = new Pitch("p", 3, 1, 0);
    Pitch prevPitch = pitch.getPreviousStep(0);
    assertEquals(prevPitch.getOctave(), 3);
    assertEquals(prevPitch.getStep(), 0);
    assertEquals(prevPitch.getAlter(), 0);
    pitch = new Pitch("p", 3, 0, 0);
    prevPitch = pitch.getPreviousStep(0);
    assertEquals(prevPitch.getOctave(), 2);
    assertEquals(prevPitch.getStep(), 6);
    assertEquals(prevPitch.getAlter(), 0);
  }

  public void testGetPreviousStepWithKeySignature() {
    KeySignature key = new KeySignature(2);
    Pitch pitch = new Pitch("p", 3, 1, 0);
    Pitch prevPitch = pitch.getPreviousStep(key);
    assertEquals(prevPitch.getOctave(), 3);
    assertEquals(prevPitch.getStep(), 0);
    assertEquals(prevPitch.getAlter(), 1);
    pitch = new Pitch("p", 3, 0, 1);
    prevPitch = pitch.getPreviousStep(key);
    assertEquals(prevPitch.getOctave(), 2);
    assertEquals(prevPitch.getStep(), 6);
    assertEquals(prevPitch.getAlter(), 0);
  }

  //---------------  //
  // getNextStep
  //---------------//
  public void testGetNextStepWithAccidental() {
    Pitch pitch = new Pitch("p", 3, 0, 0);
    Pitch nextPitch = pitch.getNextStep(0);
    assertEquals(nextPitch.getOctave(), 3);
    assertEquals(nextPitch.getStep(), 1);
    assertEquals(nextPitch.getAlter(), 0);
    pitch = new Pitch("p", 2, 6, 0);
    nextPitch = pitch.getNextStep(0);
    assertEquals(nextPitch.getOctave(), 3);
    assertEquals(nextPitch.getStep(), 0);
    assertEquals(nextPitch.getAlter(), 0);
  }

  public void testGetNextStepWithKeySignature() {
    KeySignature key = new KeySignature(2);
    Pitch pitch = new Pitch("p", 3, 2, 0);
    Pitch nextPitch = pitch.getNextStep(key);
    assertEquals(nextPitch.getOctave(), 3);
    assertEquals(nextPitch.getStep(), 3);
    assertEquals(nextPitch.getAlter(), 1);
    pitch = new Pitch("p", 3, 0, 1);
    nextPitch = pitch.getNextStep(key);
    assertEquals(nextPitch.getOctave(), 3);
    assertEquals(nextPitch.getStep(), 1);
    assertEquals(nextPitch.getAlter(), 0);
  }
}
