async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contract with account:", deployer.address);
  
    const Voting = await ethers.getContractFactory("PerfectVotingSystem");
    const voting = await Voting.deploy();
    await voting.waitForDeployment();
  
    // Use getAddress() to retrieve the contract address
    console.log("Contract deployed to:", await voting.getAddress());
  }
  
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
  