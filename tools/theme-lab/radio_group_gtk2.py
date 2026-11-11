# SPDX-License-Identifier: GPL-3.0-or-later
"""Two real GtkRadioButtons represented as one movable sample group.

Requested dimensions belong to the group. Member allocations remain separate
native measurements; grouping/selection is entirely GTK2's responsibility.
"""
from sample_contract import SAMPLES


class RadioGroup:
    def __init__(self, Gtk, backdrop=False):
        self.Gtk=Gtk
        self.widget=Gtk.VBox(homogeneous=True,spacing=0)
        name='themeLabBackdropRadio' if backdrop else 'themeLabRadio'
        first=Gtk.RadioButton.new_with_label_from_widget(None,SAMPLES['combo_a'])
        second=Gtk.RadioButton.new_with_label_from_widget(first,SAMPLES['combo_b'])
        self.members=(first,second)
        for button in self.members:
            button.set_name(name)
            self.widget.pack_start(button,True,True,0)
            # A GtkBox excludes invisible children from size_request. Make
            # members eligible for measurement before the parent is mapped.
            button.show()

    def selected(self):
        states=[bool(button.get_active()) for button in self.members]
        if sum(states)!=1: raise ValueError('GTK2 radio: native group lacks exactly one selected member')
        return states.index(True)

    def select(self, member):
        if type(member) is not int or member not in (0,1):
            raise ValueError('GTK2 radio: invalid group member')
        self.members[member].set_active(True)

    def metrics(self):
        rows=[]
        for button in self.members:
            allocation=button.get_allocation()
            natural=self.Gtk.Requisition();button.size_request(natural)
            rows.append({'allocation':[allocation.x,allocation.y,allocation.width,allocation.height],
                         'natural_request':[natural.width,natural.height],
                         'active':bool(button.get_active())})
        return rows
