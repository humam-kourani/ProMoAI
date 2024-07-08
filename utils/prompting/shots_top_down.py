"""
    This file includes example (description, model) pairs used for few-shots learning. Some process description are
    from the PET data set "Patrizio Bellan, Han van der Aa, Mauro Dragoni, Chiara Ghidini, and Simone Paolo Ponzetto.
    PET: an annotated dataset for process extraction from natural language text tasks. In Business Process Management
    Workshops 2022, Revised Selected Papers, volume 460 of Lecture Notes in Business Information Processing,
    pages 315–321. Springer, 2022".
"""


import pm4py
from pm4py.objects.conversion.powl.variants.to_petri_net import apply as to_pn
from utils.model_generation import ModelGenerator

d1 = "in this process, you can either do 'a' or 'b'. If 'a' is selected," \
     " then it can be repeated. After completing 'a' or 'b', 'c' is executed, followed by 'd'. Finally another" \
     " execution of 'a' is performed. The whole process is optional and can be skipped."


def m1():
    gen = ModelGenerator()

    def model_over_all_activities():
        child1 = model_a_b()
        child2 = model_c()
        child3 = model_d()
        child4 = model_second_a()
        order = gen.partial_order(dependencies=[(child1, child2), (child2, child3), (child3, child4)])
        return gen.xor(order, None)

    def model_a_b():
        return gen.xor(model_a(), model_b())

    def model_a():
        a = gen.activity('a')
        return gen.loop(do=a, redo=None)

    def model_b():
        return gen.activity('b')

    def model_c():
        return gen.activity('c')

    def model_d():
        return gen.activity('d')

    def model_second_a():
        return gen.activity('a')

    final_model = model_over_all_activities()

    return final_model


e1 = "a common error for this process is to add a sequential dependency 'd -> a' without creating a" \
     " copy of 'a'. This would violate the reflexivity of the partial order."

d1_2 = "in this process, you can either do 'a' or 'b'. If 'a' is selected," \
       " then it can be repeated. After completing 'a' or 'b', 'c' is executed, followed by 'd'. Finally, the process" \
       " either ends or goes back to 'a'."


def m1_2():
    gen = ModelGenerator()

    def model_over_all_activities():
        child1 = model_a_b()
        child2 = model_c()
        child3 = model_d()
        order = gen.partial_order(dependencies=[(child1, child2), (child2, child3)])
        return gen.loop(do=order, redo=None)

    def model_a_b():
        return gen.xor(model_a(), model_b())

    def model_a():
        a = gen.activity('a')
        return gen.loop(do=a, redo=None)

    def model_b():
        return gen.activity('b')

    def model_c():
        return gen.activity('c')

    def model_d():
        return gen.activity('d')

    final_model = model_over_all_activities()
    return final_model


e1_2 = "a common error for this process is to add a sequential dependency 'd -> a' or 'd -> a.copy()'" \
       " instead of creating the loop 'loop_back'. 'Going back' indicates the whole process should be repeatable."

d2 = "inventory management can proceed through restocking items or fulfilling orders. Restocking can be performed as " \
     "often as necessary. Following either restocking or order fulfillment, an inventory audit is carried out, " \
     "which then leads to data analysis. Additionally, urgent restocking needs can bypass regular restocking and " \
     "order fulfillment processes directly leading to the inventory audit. This entire process is modular and can be " \
     "repeated or skipped based on operational requirements. "


def m2():
    gen = ModelGenerator()
    restock = gen.activity('restock items')
    loop_1 = gen.loop(do=restock, redo=None)
    fulfil = gen.activity('fulfill orders')
    choice_1 = gen.xor(loop_1, fulfil)
    urgent_restock = gen.activity('urgent restock')
    choice_2 = gen.xor(choice_1, urgent_restock)
    inventory_audit = gen.activity('inventory audit')
    data_analysis = gen.activity('data analysis')
    poset_1 = gen.partial_order(dependencies=[(choice_2, inventory_audit, data_analysis)])
    final_skip_loop = gen.loop(do=None, redo=poset_1)
    final_model = final_skip_loop
    return final_model


e2 = "a common error for this process is to copy 'inventory_audit'."

d3 = "This enhanced payroll process allows for a high degree of customization and adaptation to specific " \
     "requirements. Employees' time can be tracked with the option to repeat this step as needed. Pay calculations " \
     "follows, incorporating diverse factors such as overtime, bonuses, and deductions. Subsequently, the process " \
     "facilitates the issuance of payments and the generation of detailed reports. "


def m3():
    gen = ModelGenerator()
    track_time = gen.activity('track time')
    activity_1_self_loop = gen.loop(do=track_time, redo=None)
    activity_2 = gen.activity('calculate pay')
    activity_3 = gen.activity('issue payments')
    activity_4 = gen.activity('generate reports')
    poset = gen.partial_order(dependencies=[(activity_1_self_loop, activity_2, activity_3), (activity_2, activity_4)])
    final_model = poset
    return final_model


e3 = "a common error for this process is to model a choice between activity_3 and activity_4 instead of the" \
     " concurrency."

d4 = "This system combines 4 parallel subprocesses, i.e., that are executed independently/at the same time. The first " \
     "process starts with A followed by B then a choice of C and D. The second process consists of a single activity " \
     "E which can be repeated but must be executed at least once. The third process consists of the activity F, " \
     "which can be repeated or skipped. The last process contains the parallel activities G, H, I, J with the " \
     "constrains that I must precede J and H must precede I "


def m4():
    gen = ModelGenerator()

    # subprocess 1
    a = gen.activity('a')
    b = gen.activity('b')
    choice_c_d = gen.xor(gen.activity('c'), gen.activity('d'))

    # subprocess 2
    unskippable_self_loop_e = gen.loop(do=gen.activity('e'), redo=None)

    # subprocess 3
    skippable_self_loop_f = gen.loop(do=None, redo=gen.activity('f'))

    # subprocess 4
    g = gen.activity('g')
    h = gen.activity('h')
    i = gen.activity('i')
    j = gen.activity('j')

    # combine all subprocesses
    final_model = gen.partial_order(
        dependencies=[(a, b, choice_c_d), (unskippable_self_loop_e,), (skippable_self_loop_f,), (g,), (h, i, j)])
    return final_model


e4 = "a common error for this process is to create partial orders for some subprocesses, then trying to add a" \
     " partial order as a child of another partial order."

d5 = "A customer brings in a defective computer and the CRS checks the defect and hands out a repair cost calculation " \
     "back. If the customer decides that the costs are acceptable , the process continues , otherwise she takes her " \
     "computer home unrepaired. The ongoing repair consists of two activities , which are executed , in an arbitrary " \
     "order. The first activity is to check and repair the hardware , whereas the second activity checks and " \
     "configures the software. After each of these activities , the proper system functionality is tested. If an " \
     "error is detected another arbitrary repair activity is executed , otherwise the repair is finished. "


def m5():
    gen = ModelGenerator()
    defect_check = gen.activity('Check defect')
    cost_calculation = gen.activity('Calculate repair costs')
    cancel = gen.activity('Cancel and give computer unrepaired')
    repair_hardware = gen.activity('Check and repair the hardware')
    repair_software = gen.activity('Check and configure the software')
    test_functionality_after_hardware_repair = gen.activity('Test system functionality')
    test_functionality_after_software_repair = gen.activity('Test system functionality')
    additional_hardware_repair = gen.xor(gen.activity('Perform additional hardware repairs'), None)
    additional_software_repair = gen.xor(gen.activity('Perform additional software repairs'), None)
    finish_repair = gen.activity('Finish repair')

    hardware_repair_order_dependencies = (
        repair_hardware, test_functionality_after_hardware_repair, additional_hardware_repair)

    software_repair_order_dependencies = (
        repair_software, test_functionality_after_software_repair, additional_software_repair)

    poset_full_repair = gen.partial_order(
        dependencies=[hardware_repair_order_dependencies, software_repair_order_dependencies,
                      (additional_software_repair, finish_repair), (additional_hardware_repair, finish_repair)])

    # choice between canceling or starting the repair process
    choice = gen.xor(cancel, poset_full_repair)

    # final model
    final_model = gen.partial_order(dependencies=[(defect_check, cost_calculation, choice)])

    return final_model


e5 = "a common error for this process is to create partial orders for some subprocesses, then trying to add a" \
     " partial order as a child of another partial order. Another very important error you should avoid is to" \
     " create a local choice between 'cancel' and some local activity (e.g., 'continue process') instead of" \
     " model_generation a choice between 'cancel' and the rest of the process. After canceling a process no activities" \
     " should be executable!"

d6 = "A small company manufactures customized bicycles. Whenever the sales department receives an order , " \
     "a new process instance is created. A member of the sales department can then reject or accept the order " \
     "for a customized bike. In the former case , the process instance is finished. In the latter case , " \
     "the storehouse and the engineering department are informed. The storehouse immediately processes the part " \
     "list of the order and checks the required quantity of each part. If the part is available in-house , " \
     "it is reserved. If it is not available , it is back-ordered. This procedure is repeated for each item on " \
     "the part list. In the meantime , the engineering department prepares everything for the assembling of the " \
     "ordered bicycle. If the storehouse has successfully reserved or back-ordered every item of the part list " \
     "and the preparation activity has finished , the engineering department assembles the bicycle. Afterwards " \
     ", the sales department ships the bicycle to the customer and finishes the process instance . "


def m6():
    gen = ModelGenerator()

    def model_over_all_activities():
        child1 = create_process()
        child2 = choice_accept_reject()
        child3 = finish_process()
        return gen.partial_order(dependencies=[(child1, child2), (child2, child3)])

    def create_process():
        return gen.activity('Create process instance')

    def choice_accept_reject():
        return gen.xor(accept_case(), reject_case())

    def finish_process():
        return gen.activity('Finish process instance')

    def reject_case():
        return gen.activity('Reject order')

    def accept_case():
        accept_order = gen.activity('Accept order')
        inform = gen.activity('Inform storehouse and engineering department')
        process_part_list = gen.activity('Process part list')
        prepare_assembly = gen.activity('Prepare bicycle assembly')
        assemble_bicycle = gen.activity('Assemble bicycle')
        ship_bicycle = gen.activity('Ship bicycle')
        part_loop = create_part_loop()
        return gen.partial_order(dependencies=[(accept_order, inform), (inform, process_part_list),
                                               (inform, prepare_assembly), (process_part_list, part_loop),
                                               (part_loop, assemble_bicycle), (prepare_assembly, assemble_bicycle),
                                               (assemble_bicycle, ship_bicycle)])

    def create_part_loop():
        check_part = gen.activity('Check required quantity of the part')
        check_reserve = create_check_reserve_choice()
        single_part = gen.partial_order(dependencies=[(check_part, check_reserve)])
        return gen.loop(do=single_part, redo=None)

    def create_check_reserve_choice():
        reserve = gen.activity('Reserve part')
        back_order = gen.activity('Back-order part')
        return gen.xor(reserve, back_order)

    final_model = model_over_all_activities()
    return final_model


e6 = "a common error for this process is to" \
     " create a local choice between 'reject_order' and 'accept_order' instead of" \
     " model_generation a choice between 'reject_order' and the complete complex subprocess that is executed in case" \
     " the order is accepted ('accept_poset'). This is a very important process construct where you should model" \
     " a choice between full paths and not mistakenly model a choice between the entry point of the paths. Although" \
     " the text says there is a choice between accepting or rejecting the order, you should derive from your" \
     " understanding of the context that this choice also includes all activities that are executed after accepting" \
     " an order. It does not make sense to model a choice between accept and reject the order and make the rest of" \
     " the process independent of this choice! The choice must be modeled on a higher lever: an xor between the full" \
     " path taken in case the order is accepted and the full path taken in case the order is rejected."

d7 = "A and B can happen in any order (concurrent). C and D can happen in any order. A precedes both C and D. B " \
     "precedes D"


def m7():
    gen = ModelGenerator()

    def model_over_all_activities():
        a = model_a()
        b = model_b()
        c = model_c()
        d = model_d()
        return gen.partial_order(dependencies=[(a, c), (a, d), (b, d)])

    def model_a():
        return gen.activity('a')

    def model_b():
        return gen.activity('b')

    def model_c():
        return gen.activity('c')

    def model_d():
        return gen.activity('d')

    final_model = model_over_all_activities()
    return final_model


e7 = "a common error for this process is to add a sequential dependency 'B -> C' since the text says that 'C' and 'D'" \
     " are concurrent. This conclusion is not justified and 'B' and 'C' can remain concurrent in the partial order."


SHOTS_TOP_DOWN = [(d1, m1, e1), (d1_2, m1_2, e1_2), (d6, m6, e6), (d7, m7, e7)]

if __name__ == "__main__":
    model = m6()
    pn, im, fm = to_pn(model)
    pm4py.view_petri_net(pn, im, fm)
