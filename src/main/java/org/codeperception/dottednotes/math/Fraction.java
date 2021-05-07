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
 * 
 * This file is written by Mario Lang <mlang@delysid.org>
 * for the project FreeDots -- MusicXML to braille music transcription,
 * <https://github.com/mlang/freedots>.
 */

package org.codeperception.dottednotes.math;

/** Represents an arbitrary fractional value.
 */
public class Fraction extends AbstractFraction {

  private final int numerator, denominator;

  public Fraction(final AbstractFraction fraction) {
    this(fraction.numerator(), fraction.denominator());
  }

  public Fraction(final int numerator) {
    this(numerator, 1);
  }

  public Fraction(final int numerator, final int denominator) {
    if (denominator == 0) throw new ArithmeticException("denominator is zero");
    this.numerator = numerator;
    this.denominator = denominator;
  }

  public int numerator() {
    return numerator;
  }

  public int denominator() {
    return denominator;
  }

  public Fraction simplify() {
    final int gcd = greatestCommonDivisor();
    return (gcd == 1) ? this : new Fraction(numerator / gcd, denominator / gcd);
  }

  public static final Fraction ZERO = new Fraction(0);
}
