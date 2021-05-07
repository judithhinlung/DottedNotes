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
import org.codeperception.dottednotes.math.Fraction;

public class Voice {

  int number;
  int staffNumber;
  ArrayList<MeasureElement> elements;

  public Voice(int number) {
    this.number = number;
    this.elements = new ArrayList<MeasureElement>();
  }

  public Voice(int number, int staffNumber) {
    this.number = number;
    this.staffNumber = staffNumber;
    this.elements = new ArrayList<MeasureElement>();
  }

  public int getNumber() {
    return this.number;
  }

  public int getStaffNumber() {
    return this.staffNumber;
  }

  public ArrayList<MeasureElement> getElements() {
    return this.elements;
  }

  public void addElement(MeasureElement element) {
    if ((element instanceof Note) || (element instanceof Chord)) {
      this.elements.add(element);
    }
  }

  public void removeElement(MeasureElement element) {
    if (!(element instanceof Note) && !(element instanceof Chord)) {
      return;
    }
    int removeIndex = 0;
    Fraction duration = element.getDuration();
    for (int i = 0; i < this.elements.size(); i++) {
      MeasureElement current = this.elements.get(i);
      if (
        (current.getMoment().equals(element.getMoment())) &&
        (current.getDuration().equals(element.getDuration()))
      ) {
        removeIndex = i;
      }
    }
    this.elements.remove(removeIndex);
    resetElements(duration, removeIndex);
  }

  /**
   * Shifts voice elements back by  the given duration
   * starting at the given index
   */
  public void resetElements(Fraction duration, int startIndex) {
    for (int i = startIndex; i < this.elements.size(); i++) {
      MeasureElement element = this.elements.get(i);
      Fraction newMoment = element.getMoment().subtract(duration);
      element.setMoment(newMoment);
    }
  }
}
