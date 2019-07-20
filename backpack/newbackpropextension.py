import warnings

FAIL_ERROR = "ERROR"
FAIL_WARN = "WARN"
FAIL_SILENT = "SILENT"


class NewBackpropExtension:
    """
    Base class for the new type of BackpropExtension for BackPACK.

    Descendants of this class need to define in what field to save results
    and provide a mapping from Module classes to ModuleExtension instances.

    They can then be passed to the Backpack context manager, i.e.,
    ```
    with backpack(NewPackpropExtension("myfield", module_to_extensions)):
        loss(model(X), Y).backward()

        for p in model.parameters():
            print(p.myfield)
    ```
    """

    def __init__(self, savefield, module_exts, fail_mode=FAIL_ERROR):
        """
        Parameters
        ----------
        savefield : str

        module_exts : dict
            Dictionary mapping module classes to `ModuleExtension` instances
        fail_mode : str, optional
            Behavior when encountering an unknown layer.
            Can be
            - "ERROR": raise a NotImplementedError
            - "WARN": raise a UserWarning
            - "SILENT": skip the module silently
        """
        self.__savefield = savefield
        self.__module_extensions = module_exts
        self.__fail_mode = fail_mode

    def __get_module_extension(self, module):
        module_extension = self.__module_extensions.get(module.__class__)

        if module_extension is None:
            if self.__fail_mode is FAIL_ERROR:
                raise NotImplementedError(
                    "Extension saving to {} ".format(self.__savefield) +
                    "does not have an extension for " +
                    "Module {}".format(module.__class__)
                )
            elif self.__fail_mode is FAIL_WARN:
                warnings.warn(
                    "Extension saving to {} ".format(self.__savefield) +
                    "does not have an extension for " +
                    "Module {}".format(module.__class__)
                )
            elif self.__fail_mode is FAIL_SILENT:
                no_op = lambda *args: None
                return no_op

        return module_extension.apply

    def apply(self, module, grad_input, grad_output):
        module_extension = self.__get_module_extension(module)
        module_extension(self, module, grad_input, grad_output)
