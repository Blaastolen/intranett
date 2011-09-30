from Products.CMFCore.permissions import setDefaultRoles

AssignTasksToUsers = "intranett.task: Assign tasks to users"
setDefaultRoles(AssignTasksToUsers, ('Manager', ))
