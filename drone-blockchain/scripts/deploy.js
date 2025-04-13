const hre = require("hardhat");

async function main() {
  const DroneConsensus = await hre.ethers.getContractFactory("DroneConsensus");
  const droneConsensus = await DroneConsensus.deploy();          // 배포
  await droneConsensus.waitForDeployment();                      // 배포 완료 대기 (deployed() ❌, waitForDeployment() ⭕)

  console.log("Contract deployed to:", await droneConsensus.getAddress()); // v6에서는 address가 아니라 getAddress() 호출해야 해
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

