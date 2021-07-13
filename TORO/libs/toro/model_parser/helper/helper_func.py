from Amalthea2PyCPA import Parser

xml_file = "dummy.amxmi"
parser = Parser.Parser("/home/alexb/Documents/Masterarbeit/Wirkketten_Tool/TORO/data/AmaltheaModels/amaltheaModels/model.amxmi")

# parser.get_infoContents_pathsOnly("Task", verifyPaths=True)

# parser.get_infoContents_pathsOnly(source="Task", destination="Ticks", verifyPaths=True)

# parser.get_infoContents_pathsOnly(source="Task", destination="ExecutionNeed", verifyPaths=True)

# parser.get_infoAssociations_pathsOnly(source="Task", destination="TaskAllocation", verifyPaths=True)

# parser.get_classInfo("PeriodicStimulus")

# parser.get_classInfo("LabelAccess")


# parser.get_infoContents_pathsOnly("EventChain", verifyPaths=True)

# parser.get_classInfo("EventChain")

# parser.get_infoAssociations("EventChain", "Task")

# parser.get_classInfo("EventChain")


# parser.get_infoAssociations("EventChain", "EventChainLatencyConstraint")
# parser.get_infoAssociations_pathsOnly("EventChain", "EventChainLatencyConstraint")
# parser.get_classInfo("EventChainLatencyConstraint")


parser.get_infoContents_pathsOnly("DelayConstraint")
# parser.get_infoAssociations(source="DelayConstraint", destination="Label")
# parser.get_infoContents(source='Task', destination='TaskRunnableCall')
# parser.get_infoContents_pathsOnly(source='Task', destination='TaskRunnableCall')


