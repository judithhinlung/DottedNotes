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

/**
 * A figured bass element takes its position from the first regular note.
 * Figures are ordered from top to bottom.
 */
public class FiguredBass extends MeasureElement {

  /**
   * @param duration  optional, indicates changes of figures under the note
   * @param number  figure number
   * @param prefix preceding the figure number
   * @param Suffix  value following the figured number, valid suffixes include all
   * valid prefix and suffix symbols.
   */
  int duration = 0;
  String prefix;
  int number;
  String suffix;

  public FiguredBass(Measure measure, String prefix, int number, String suffix)
    throws IllegalArgumentException {
    super(measure);
    if (Utils.contains(prefix, validPrefixes)) {
      throw new IllegalArgumentException("Invalid figured bass prefix: " + prefix);
    }
    if (
      !(Utils.contains(suffix, validPrefixes)) || (Utils.contains(suffix, validSuffixes))
    ) {
      throw new IllegalArgumentException("Invalid figured bass suffix: " + suffix);
    }
    this.number = number;
    this.prefix = prefix;
    this.suffix = suffix;
  }

  public FiguredBass(Measure measure, int number) {
    super(measure);
    this.number = number;
  }

  public void addPrefix(String prefix) throws IllegalArgumentException {
    if (Utils.contains(prefix, validPrefixes)) {
      throw new IllegalArgumentException("Invalid figured bass prefix: " + prefix);
    }
    this.prefix = prefix;
  }

  public void addSuffix(String suffix) throws IllegalArgumentException {
    if (
      !(Utils.contains(suffix, validPrefixes)) || (Utils.contains(suffix, validSuffixes))
    ) {
      throw new IllegalArgumentException("Invalid figured bass suffix: " + suffix);
    }
    this.suffix = suffix;
  }

  public void setDuration(int duration) {
    this.duration = duration;
  }

  public String getPrefix() {
    return this.prefix;
  }

  public int getNumber() {
    return this.number;
  }

  public String getSuffix() {
    return this.suffix;
  }

  public int getDuration(int duration) {
    return this.duration;
  }

  private String[] validPrefixes = new String[] {
    "plus",
    "sharp",
    "flat",
    "natural",
    "double-sharp",
    "flat-flat",
    "sharp-sharp",
  };
  private String[] validSuffixes = new String[] { "slash", "backslash", "vertical" };
}
