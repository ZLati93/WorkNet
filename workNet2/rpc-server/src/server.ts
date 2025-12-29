import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import dotenv from 'dotenv';

dotenv.config();

const PROTO_PATH = './src/proto/worknet.proto';
const PORT = process.env.RPC_PORT || 5001;

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true
});

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition);
const worknetProto = protoDescriptor.worknet as any;

const server = new grpc.Server();

// Add your RPC service implementations here
server.addService(worknetProto.WorkNetService.service, {
  // Implement your RPC methods here
});

server.bindAsync(`0.0.0.0:${PORT}`, grpc.ServerCredentials.createInsecure(), (err, port) => {
  if (err) {
    console.error('Failed to start RPC server:', err);
    return;
  }
  server.start();
  console.log(`RPC Server is running on port ${port}`);
});

