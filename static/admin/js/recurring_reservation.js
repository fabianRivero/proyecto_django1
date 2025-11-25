document.addEventListener("DOMContentLoaded", () => {
    function toggleDaysField() {
        const ruleTypeField = document.querySelector("#id_rule_type");
        const daysWrapper = document.querySelector("#id_days_of_week").closest(".form-row") 
            || document.querySelector("#id_days_of_week").closest(".field-days_of_week");

        if (!ruleTypeField || !daysWrapper) return;

        if (ruleTypeField.value === "weekly") {
            daysWrapper.style.display = "block";
        } else {
            daysWrapper.style.display = "none";
        }
    }

    const ruleTypeField = document.querySelector("#id_rule_type");

    if (ruleTypeField) {
        ruleTypeField.addEventListener("change", toggleDaysField);
        toggleDaysField(); 
    }
});
