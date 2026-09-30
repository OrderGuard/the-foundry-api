document.addEventListener("DOMContentLoaded", function () {
    console.log("Reward config loaded");

    const rewardType = document.getElementById("id_reward_type");

    function toggleRewardFields() {
        console.log("Reward type:", rewardType.value);

        // Find the field containers
        const discountRow = document.getElementById("id_discount_type")?.closest("div");
        const valueRow = document.getElementById("id_value")?.closest("div");
        const freeItemRow = document.getElementById("id_free_item")?.closest("div");

        console.log(discountRow, valueRow, freeItemRow);

        if (rewardType.value === "free_item") {
            discountRow && (discountRow.style.display = "none");
            valueRow && (valueRow.style.display = "none");
            freeItemRow && (freeItemRow.style.display = "");
        } else {
            discountRow && (discountRow.style.display = "");
            valueRow && (valueRow.style.display = "");
            freeItemRow && (freeItemRow.style.display = "none");
        }
    }

    toggleRewardFields();

    rewardType.addEventListener("change", toggleRewardFields);
});

