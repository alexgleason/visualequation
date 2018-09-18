# visualequation is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# visualequation is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" The module that manages the editing equation. """
import os
import types

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from . import eqtools
from . import conversions
from . import symbols

# TODO (maybe in a different module)
class EqHisto:
    def __init__(self, eq):
        pass

class Eq(QLabel):
    def __init__(self, eq, temp_dir, parent):
        super().__init__(parent)

        self.parent = parent
        self.eq_hist = [(list(eq), 0)]
        self.eq_hist_index = 0
        self.eq_buffer = []
        self.eq = list(eq) # It will be mutated by the replace functions
        self.temp_dir = temp_dir
        self.sel_index = 0
        self.sel_right = True
        self._set_sel()

    def event(self, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            self.next_sel()
            # The True value prevents the event to be sent to other objects
            return True
        else:
            return QLabel.event(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.next_sel()
        elif event.button() == Qt.RightButton:
            self.previous_sel()
        else:
            QLabel.mousePressEvent(self, event)

    def keyPressEvent(self, event):
        if QApplication.keyboardModifiers() != Qt.ControlModifier:
            self.on_key_pressed_no_ctrl(event)
        else:
            self.on_key_pressed_ctrl(event)

    def on_key_pressed_no_ctrl(self, event):
        # 0-9 or A-Z or a-z exluding Ctr modifier
        try:
            code = ord(event.text())
            if (48 <= code <= 57 or 65 <= code <= 90 or 97 <= code <= 122) \
               and QApplication.keyboardModifiers() != Qt.ControlModifier:
                self.insert(event.text())
        except TypeError:
            pass
        try:
            self.insert(symbols.ASCII_LATEX_TRANSLATION[event.text()])
        except KeyError:
            pass
        key = event.key()
        if key == Qt.Key_Up:
            self.insert_substituting(symbols.SUPERINDEX)
        elif key == Qt.Key_Down:
            self.insert_substituting(symbols.SUBINDEX)
        elif key == Qt.Key_Right:
            self.next_sel()
        elif key == Qt.Key_Left:
            self.previous_sel()
        elif key == Qt.Key_Backslash:
            self.insert(r'\backslash')
        elif key == Qt.Key_AsciiTilde:
            self.insert(r'\sim')
        elif key == Qt.Key_Backspace or key == Qt.Key_Delete:
            self.remove_sel()
        elif key == Qt.Key_Space:
            self.insert(r'\,')

    def on_key_pressed_ctrl(self, event):
        pass

    def _set_sel(self):
        """ Set pixmap to the equation boxed in the
        selection indicated by self.sel_index, which can be freely set
        by the caller before calling this function.

        (The box is the way the user know which block of the eq is editing).
        """
        if not 0 <= self.sel_index < len(self.eq):
            raise ValueError('Provided index outside the equation.')
        # Avoid pointing to a intermediate Juxt
        # That avoids selecting partial products inside a product
        elif self.is_intermediate_JUXT(self.sel_index):
            cond = True
            while cond:
                self.sel_index += 1
                cond = self.is_intermediate_JUXT(self.sel_index)

        # Calculate the latex code of eq boxed in block given by the selection
        sel_eq = eqtools.sel_eq(self.eq, self.sel_index, self.sel_right)
        sel_png = conversions.eq2png(sel_eq, None, None,
                                     self.temp_dir)
        self.setPixmap(QPixmap(sel_png))
        # This helps catching all the keys
        self.setFocus()

    def is_intermediate_JUXT(self, index):
        """
        Check whether if index points to a JUXT that is the argument of
        other JUXT.
        """
        if self.eq[index] == symbols.JUXT:
            cond, _, _ = eqtools.is_arg_of_JUXT(self.eq, index)
            if cond:
                return True
        return False

    def next_sel(self):
        """ Set image to the next selection according to self.sel_index. """
        if not self.sel_right:
            self.sel_right = True
        elif self.sel_index == len(self.eq) - 1:
            self.sel_index = 0
        else:
            self.sel_index += 1
        if self.is_intermediate_JUXT(self.sel_index):
            cond = True
            while cond:
                self.sel_index += 1
                cond = self.is_intermediate_JUXT(self.sel_index)

        self._set_sel()

    def previous_sel(self):
        """ Set image to the next selection according to self.sel_index. """
        if self.sel_right:
            self.sel_right = False
        elif self.sel_index == 0:
            self.sel_index = len(self.eq) - 1
        else:
            self.sel_index -= 1
        if self.is_intermediate_JUXT(self.sel_index):
            cond = True
            while cond:
                self.sel_index -= 1
                cond = self.is_intermediate_JUXT(self.sel_index)

        self._set_sel()

    def insert(self, oper):
        """
        Insert a symbol next to selection by Juxt and, if it is an operator,
        set all the arguments to NewArg.
        """
        def replace_op_in_eq(op):
            """
            Given an operator, it is replaced in self.eq according to
            the rules of above. It also modify self.sel_index to point to
            the smartest block.
            """            
            if isinstance(op, str):
                if self.eq[self.sel_index] == symbols.NEWARG:
                    self.eq[self.sel_index] = op
                else:
                    if self.sel_right:
                        self.sel_index = eqtools.insertrbyJUXT(self.eq,
                                                               self.sel_index,
                                                               [op])
                    else:
                        self.sel_index = eqtools.insertlbyJUXT(self.eq,
                                                               self.sel_index,
                                                               [op])
            elif isinstance(op, symbols.Op):
                opeq = [op] + [symbols.NEWARG]*op.n_args
                if self.eq[self.sel_index] == symbols.NEWARG:
                    self.eq[self.sel_index:self.sel_index+1] = opeq
                    self.sel_index += 1
                else:
                    if self.sel_right:
                        self.sel_index \
                            = 1 + eqtools.insertrbyJUXT(self.eq,
                                                        self.sel_index,
                                                        opeq)
                    else:
                        self.sel_index \
                            = 1 + eqtools.insertlbyJUXT(self.eq,
                                                        self.sel_index,
                                                        opeq)
            else:
                raise ValueError('Unknown type of operator %s' % op)

        if isinstance(oper, types.FunctionType):
            op = oper(self.parent)
            if op:
                replace_op_in_eq(op)
            else:
                return None
        else:
            replace_op_in_eq(oper)

        self.sel_right = True
        self._set_sel()
        self.add_eq2hist()

    def insert_substituting(self, oper):
        """
        Given an operator, the equation block pointed by self.sel_index
        is replaced by that operator and the selection is used as follows:

        If op is a str, just replace it.

        If op is an unary operator, put the selected block as the argument
        of the operator.

        If the operator has more than one argument, put the selected block
        as the first argument of the operator. Put NewArg symbols in the
        rest of the arguments.

        If the operator has more than one argument, selection index is
        changed to the second argument of the operator because the user
        probably will want to change that argument.
        """
        def replace_op_in_eq(op):
            """
            Given an operator, it is replaced in self.eq according to
            the rules of above. It also modify self.sel_index to point to
            the smartest block.
            """
            if isinstance(op, str):
                eqtools.replaceby(self.eq, self.sel_index, [op])
            elif isinstance(op, symbols.Op) and op.n_args == 1:
                self.eq.insert(self.sel_index, op)
            elif isinstance(op, symbols.Op) and op.n_args > 1:
                index_end_arg1 = eqtools.nextblockindex(self.eq, self.sel_index)
                self.eq[self.sel_index:index_end_arg1] = [op] \
                                    + self.eq[self.sel_index:index_end_arg1] \
                                    + [symbols.NEWARG] * (op.n_args-1)
                self.sel_index = index_end_arg1+1
            else:
                raise ValueError('Unknown operator passed.')

        if isinstance(oper, types.FunctionType):
            op = oper(self.parent)
            if op:
                replace_op_in_eq(op)
            else:
                return None
        else:
            replace_op_in_eq(oper)

        self.sel_right = True
        self._set_sel()
        self.add_eq2hist()

    def add_eq2hist(self):
        """
        Save current equation to the historial and delete any future elements
        from this point
        """
        self.eq_hist[self.eq_hist_index+1:] = [(list(self.eq), self.sel_index)]
        self.eq_hist_index += 1

    def remove_sel(self):
        """
        If self.sel_index points to the first or second arg of a Juxt,
        it removes the Juxt and leaves the other argument in its place.
        Else, it removes the block pointed and put a NEWARG.
        """
        cond, JUXT_index, other_arg_index = eqtools.is_arg_of_JUXT(
            self.eq, self.sel_index)
        if cond:
            JUXT_end = eqtools.nextblockindex(self.eq, JUXT_index)
            # If sel_index is the first argument (instead of the second)
            if JUXT_index + 1 == self.sel_index:
                self.eq[JUXT_index:JUXT_end] = self.eq[
                    other_arg_index:JUXT_end]
            else:
                self.eq[JUXT_index:JUXT_end] = self.eq[
                    other_arg_index:self.sel_index]
            self.sel_index = JUXT_index
        else:
            eqtools.replaceby(self.eq, self.sel_index, [symbols.NEWARG])

        self.sel_right = True
        self._set_sel()
        self.add_eq2hist()

    def open_eq(self):
        neweq = conversions.open_eq(self.parent)
        if neweq != None:
            self.eq = list(neweq)
            self.sel_index = 0
            self._set_sel()
            self.add_eq2hist()

    def save_eq(self):
        items = ["PNG", "PDF", "EPS", "SVG"]
        msg = "Select format:\n\nNote: Eqs. can only be recovered\n" \
              + "from PNG and PDF."
        item, ok = QInputDialog.getItem(self.parent, "Save equation",
                                        msg, items, 0, False)
        if not ok:
            return None
        # Implement a Save File dialog
        # The staticmethod does not accept default suffix
        itemfilter = item + " (*." + item.lower() + ")"
        dialog = QFileDialog(self.parent, 'Save equation', '', itemfilter)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix(item.lower())
        dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
        if not dialog.exec_():
            return
        filename = dialog.selectedFiles()[0]
        # Implement an Overwrite? dialog since the default one does not
        # check filename when default suffix extension has to be added
        if os.path.exists(filename):
            msg = 'A file named "' + os.path.basename(filename) \
                  + '" already exists. Do you want to replace it?'
            ret_val = QMessageBox.question(self.parent, 'Overwrite', msg)
            if ret_val != QMessageBox.Yes:
                return
        if item == 'PNG':
            conversions.eq2png(self.eq, 600, None, self.temp_dir,
                               filename, True)
        elif item == 'PDF':
            conversions.eq2pdf(self.eq, self.temp_dir, filename)
        elif item == 'SVG':
            conversions.eq2svg(self.eq, self.temp_dir, filename)
        elif item == 'EPS':
            conversions.eq2eps(self.eq, self.temp_dir, filename)

    def recover_prev_eq(self):
        """ Recover previous equation from the historial, if any """
        if self.eq_hist_index != 0:
            self.eq_hist_index -= 1
            eq, sel_index = self.eq_hist[self.eq_hist_index]
            self.eq = list(eq)
            self.sel_index = sel_index
            self._set_sel()

    def recover_next_eq(self):
        """ Recover next equation from the historial, if any """
        if self.eq_hist_index != len(self.eq_hist)-1:
            self.eq_hist_index += 1
            eq, sel_index = self.eq_hist[self.eq_hist_index]
            self.eq = list(eq)
            self.sel_index = sel_index
            self._set_sel()

    def sel2eqbuffer(self):
        """ Copy block pointed by self.sel_index to self.eq_buffer """
        end_sel_index = eqtools.nextblockindex(self.eq, self.sel_index)
        self.eq_buffer = self.eq[self.sel_index:end_sel_index]

    def eqbuffer2sel(self):
        """
        Append self.eq_buffer to the right of the block pointed by
        self.sel_index. If the block is a NEWARG, just replace it.
        """
        if self.eq_buffer != []:
            if self.eq[self.sel_index] == symbols.NEWARG:
                self.eq[self.sel_index:self.sel_index+1] = self.eq_buffer
            else:
                if self.sel_right:
                    self.sel_index = eqtools.insertrbyJUXT(self.eq,
                                                           self.sel_index,
                                                           self.eq_buffer)
                else:
                    self.sel_index = eqtools.insertlbyJUXT(self.eq,
                                                           self.sel_index,
                                                           self.eq_buffer)
            self.sel_right = True
            self._set_sel()
            self.add_eq2hist()

    def left_NEWARG(self):
        """
        Append by JUXT a NEWARG at the left of the block pointed by
        self.sel_index.
        """
        self.eq[self.sel_index:self.sel_index] = [symbols.JUXT, symbols.NEWARG]
        self.sel_index += 1
        self._set_sel()
        self.add_eq2hist()
