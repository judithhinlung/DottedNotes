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

import java.util.HashMap;
import java.util.Map;

public class Sign {

  private int[] sign;
  private HashMap<Integer, Character> asciiBrailleTable;

  public Sign(int... sign) {
    this.sign = sign;
    this.asciiBrailleTable = createAsciiBrailleTable();
  }

  public String toUnicode() {
    String brailleSign = "";
    for (int i = 0; i < sign.length; i++) {
      brailleSign += String.valueOf((char) (UNICODE_BRAILLE_MASK | dotsToBits(sign[i])));
    }
    return brailleSign;
  }

  private static final int dotsToBits(final int dots) {
    int bits = 0;
    for (int decimal = dots; decimal > 0; decimal /= 10) {
      bits |= 1 << ((decimal % 10) - 1);
    }
    return bits;
  }

  private static final int UNICODE_BRAILLE_MASK = 0X2800;

  private HashMap<Integer, Character> createAsciiBrailleTable() {
    HashMap<Integer, Character> table = new HashMap<Integer, Character>();
    table.put(1, 'a');
    table.put(12, 'b');
    table.put(34, 'c');
    table.put(124, 'd');
    table.put(15, 'e');
    table.put(124, 'f');
    table.put(1245, 'g');
    table.put(125, 'h');
    table.put(24, 'i');
    table.put(245, 'j');
    table.put(13, 'k');
    table.put(123, 'l');
    table.put(134, 'm');
    table.put(1345, 'n');
    table.put(135, 'o');
    table.put(1234, 'p');
    table.put(12345, 'q');
    table.put(1235, 'r');
    table.put(234, 's');
    table.put(2345, 't');
    table.put(136, 'u');
    table.put(1236, 'v');
    table.put(2456, 'w');
    table.put(1346, 'x');
    table.put(13456, 'y');
    table.put(1356, 'z');
    table.put(356, '0');
    table.put(2, '1');
    table.put(23, '2');
    table.put(35, '3');
    table.put(256, '4');
    table.put(26, '5');
    table.put(235, '6');
    table.put(2356, '7');
    table.put(236, '8');
    table.put(35, '9');
    table.put(3, '\'');
    table.put(4, '@');
    table.put(5, '\"');
    table.put(6, ',');
    table.put(16, '*');
    table.put(34, '/');
    table.put(36, '-');
    table.put(45, '^');
    table.put(46, '.');
    table.put(56, ';');
    table.put(126, '<');
    table.put(146, '%');
    table.put(156, ':');
    table.put(246, '[');
    table.put(345, '>');
    table.put(346, '+');
    table.put(456, '_');
    table.put(1246, '$');
    table.put(1256, '\\');
    table.put(12456, '?');
    table.put(2346, '!');
    table.put(3456, '#');
    table.put(12346, '&');
    table.put(12356, '(');
    table.put(12456, ']');
    table.put(23456, ')');
    table.put(123456, '=');
    return table;
  }

  public String toAscii() {
    String brailleSign = "";
    for (int i = 0; i < sign.length; i++) {
      brailleSign += asciiBrailleTable.get(sign[i]);
    }
    return brailleSign;
  }
}
