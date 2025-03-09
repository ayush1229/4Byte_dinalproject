const { expect } = require("chai");

describe("PerfectVotingSystem", function () {
  it("Should deploy the PerfectVotingSystem contract", async function () {
    const PerfectVotingSystem = await ethers.getContractFactory("PerfectVotingSystem");
    const perfectVotingSystem = await PerfectVotingSystem.deploy();
    await perfectVotingSystem.deployed();
    expect(perfectVotingSystem.address).to.properAddress;
  });

  it("Should create a voting session correctly", async function () {
    const PerfectVotingSystem = await ethers.getContractFactory("PerfectVotingSystem");
    const perfectVotingSystem = await PerfectVotingSystem.deploy();
    await perfectVotingSystem.deployed();

    const options = ["Option 1", "Option 2"];
    await perfectVotingSystem.createVotingSession("Test Session", options, 3600);

    const sessionCount = await perfectVotingSystem.getSessionCount();
    expect(sessionCount).to.equal(1);
  });

  it("Should allow voting and emit event", async function () {
    const [owner] = await ethers.getSigners();
    const PerfectVotingSystem = await ethers.getContractFactory("PerfectVotingSystem");
    const perfectVotingSystem = await PerfectVotingSystem.deploy();
    await perfectVotingSystem.deployed();

    const options = ["Option 1", "Option 2"];
    await perfectVotingSystem.createVotingSession("Test Session", options, 3600);

    await expect(perfectVotingSystem.vote(0, "Option 1"))
      .to.emit(perfectVotingSystem, "Voted")
      .withArgs(0, owner.address, "Option 1");

    const results = await perfectVotingSystem.getResults(0);
    expect(results[1][0]).to.equal(1); // Option 1 should have 1 vote
  });
});
